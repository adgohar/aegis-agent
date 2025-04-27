import os
import requests
from typing import List

from pydantic import BaseModel

from backend.models.models import Event, Location, Risk
from backend.services.db_service import DBService
from backend.services.gpt_service import GPTService


class EventDetectionService:
    def __init__(self):
        self.db_service = DBService()
        self.news_api_key = os.getenv("NEWS_API_KEY")
        self.gpt_service = GPTService()

    def process_events(self, query: str, page_size: int = 10, from_date: str = None, to_date: str = None) -> List[Event]:
        """
        Fetch, process, and store events: extract events from articles, assign risk categories,
        and assign locations.

        Parameters:
        - query: The full-text search query for fetching news articles.
        - page_size: Number of articles to fetch.
        - from_date: (Optional) The earliest publication date (YYYY-MM-DD).
        - to_date: (Optional) The latest publication date (YYYY-MM-DD).

        Returns:
        - A list of Event objects.
        """
        # Step 1: Fetch events from articles using the new parameters
        events = self.fetch_news(query, page_size, from_date, to_date)

        # Step 2: Assign risk categories and locations to each event
        for event in events:
            self.assign_risk_categories(event)
            self.assign_location(event)

        # Step 3: Save processed events to the database
        self.db_service.save_events(events)

        return events

    def fetch_news(self, query: str, page_size: int = 10, from_date: str = None, to_date: str = None) -> List[Event]:
        """
        Fetch news articles using NewsAPI and return a list of Event objects.

        Parameters:
        - query: The search query string (supports Boolean operators like OR).
        - page_size: Number of articles to retrieve (1 to 100).
        - from_date: (Optional) Start date for articles (format: YYYY-MM-DD).
        - to_date: (Optional) End date for articles (format: YYYY-MM-DD).

        Returns:
        - A list of Event objects created from the articles.
        """
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": query,
            "apiKey": self.news_api_key,
            "pageSize": page_size
        }
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            articles = response.json().get("articles", [])

            events = []
            for article in articles:
                event = self.extract_event_from_article(article)
                if event:
                    events.append(event)

            return events
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Error fetching news: {e}")

    def extract_event_from_article(self, article: dict) -> Event:
        """
        Extract an event from a news article using GPT. If the article does not describe an event,
        return None.
        """
        system_prompt = (
            "You are an expert supply chain analyst. Your task is to determine if a news article "
            "describes an event that could impact supply chains. Events might include floods, law changes, "
            "strikes, cyberattacks, or other disruptions.\n\n"
            "Rules:\n"
            "1. An event is a specific occurrence or development that has a potential impact on supply chains. "
            "   General observations, industry overviews, or speculative pieces are not considered events.\n"
            "2. If the article does not describe an event, respond with: {\"is_event\": false}.\n"
            "3. If the article describes an event, extract:\n"
            "   - A concise title summarizing the event.\n"
            "   - A detailed description of the event, including specific entities, locations, systems, and potential impacts.\n"
            "   - Set `is_event` to true.\n\n"
            "Output format according to schema, with the following fields relevant for this task:\n"
            "{\n"
            "  \"is_event\": true,\n"
            "  \"title\": \"<Event Title>\",\n"
            "  \"description\": \"<Event Description>\"\n"
            "}\n\n"
            "Examples:\n"
            "1. **Valid Event**:\n"
            "   Input:\n"
            "   Article Title: \"Cybersecurity Risk to DNA Sequencers\"\n"
            "   Article Content: \"Security vulnerabilities in DNA sequencing devices could disrupt crucial clinical research.\"\n"
            "   Output:\n"
            "   {\n"
            "     \"is_event\": true,\n"
            "     \"title\": \"Cybersecurity Vulnerabilities in DNA Sequencers\",\n"
            "     \"description\": \"Security vulnerabilities have been found in the DNA sequencing devices iSeq 100, "
            "     developed by manufacturer Illumina. The devices were found to be running an insecure BIOS implementation, "
            "     exposing them to malware and ransomware attacks. These vulnerabilities could disrupt critical clinical research.\"\n"
            "   }\n\n"
            "2. **Not an Event**:\n"
            "   Input:\n"
            "   Article Title: \"China as the Sole Manufacturing Superpower\"\n"
            "   Article Content: \"China is currently the world's sole manufacturing superpower, highlighting its production capabilities.\"\n"
            "   Output:\n"
            "   {\n"
            "     \"is_event\": false\n"
            "   }\n"
        )

        user_prompt = (
            f"Article Title: {article.get('title', 'No Title')}\n"
            f"Article Content: {article.get('description', 'No Content Available')}\n\n"
            "Determine if this article describes an event that could impact supply chains and respond accordingly."
        )

        try:
            response = self.gpt_service.call_gpt_with_schema(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                schema=Event
            )

            if not response.is_event:
                return None

            return Event(
                id=article.get("url"),
                title=response.title,
                description=response.description,
                risk_categories=None,  # To be assigned later
                timestamp=article.get("publishedAt"),
                location=None,
                source_name=article.get("source", {}).get("name"),
                author=article.get("author"),
                url=article.get("url"),
                is_event=response.is_event
            )
        except Exception as e:
            print(f"Error extracting event: {e}")
            return None

    def assign_risk_categories(self, event: Event) -> Event:
        """
        Assign risk categories to an event using GPT.
        """

        system_prompt = (
            "You are an expert risk analyst. Your task is to classify events into risk categories based on "
            "the Cambridge Risk Taxonomy.\n\n"
            "The taxonomy has three levels:\n"
            "- Class: Broadest category (e.g., Geopolitical, Environmental).\n"
            "- Family: Subcategories within each class.\n"
            "- Type: Specific examples to guide your classification.\n\n"
            "Rules for classification:\n"
            "1. Always assign at least one class to every event.\n"
            "2. Assign families only when they are relevant. If no family fits well, leave the class unaccompanied.\n"
            "3. If multiple families fit well within a class, you may assign more than one. However, choose only those that are highly relevant.\n"
            "4. Use the types as context to guide your decisions but do not include them in the output.\n\n"
            "Output format:\n"
            "- A list of Risk objects, each with:\n"
            "  - `class_name`: The main risk category.\n"
            "  - `families`: An optional array of subcategories.\n"
        )

        risk_prompt = (
            f"Event Title: {event.title}\n"
            f"Event Description: {event.description}\n\n"
            "Classify this event into one or more risk categories using the Cambridge Risk Taxonomy.\n\n"
            "The taxonomy includes the following classes and families:\n\n"
            "1. Financial:\n"
            "   - Economic Outlook:\n"
            "     - Recession, Stagnation, Contraction, Credit Crisis, Steady Growth, Expansion, Acceleration, Peak\n"
            "   - Economic Variables:\n"
            "     - Commodity Price Fluctuation, Inflation, Interest Rates\n"
            "   - Market Crisis:\n"
            "     - Asset Bubble, Bank Run, Sovereign Debt Crisis, Flash Crash, Fraudulent Market Manipulation, Cryptocurrency Failure, Reserve Currency Shift\n"
            "   - Trading Environment:\n"
            "     - Tariff Dispute, Cartel Manipulates Market, Organised Crime\n"
            "   - Company Outlook:\n"
            "     - Hostile Takeover, Credit Rating Downgrade, Investor Negative Outlook\n"
            "   - Competition:\n"
            "     - Disruptive Competitor, Aggressive Competitor, Fraudulent Competitor, Intellectual Property Theft\n"
            "   - Counterparty:\n"
            "     - Supplier Failure, Customer Failure, Government Failure, Creditor Failure, Counterparty Fraud\n\n"
            "2. Geopolitical:\n"
            "   - Business Environment (Country Risk):\n"
            "     - Talent Availability, Industrial Action, Minimum Wage Hike, Sanctions, Territorial Disputes, Logistics Restrictions\n"
            "   - Corruption & Crime:\n"
            "     - Corruption Deterioration, Crime Wave/Piracy Increase, Slavery Practices\n"
            "   - Government Business Policy:\n"
            "     - Emerging Regulation, Corporation Tax Rate Hike, Diverted Profits Tax, Nationalisation, Confiscation of Assets, Privatisation, License Revocation\n"
            "   - Change in Government:\n"
            "     - Nationalism/Protectionism, Left-Wing Radicalism, Right-Wing Radicalism, Populism, Environmentalism\n"
            "   - Political Violence:\n"
            "     - Social Unrest, Terrorism, Subnational Conflict & Civil War, Coup d’État\n"
            "   - Interstate Conflict:\n"
            "     - Conventional Military War, Asymmetric War, Nuclear War, Cold War\n\n"
            "3. Technology:\n"
            "   - Disruptive Technology:\n"
            "     - E-Commerce, Gig Economy, Artificial Intelligence, 5G Technology, Blockchain, Robotics & Automation, Augmented/Virtual Reality, Cryptocurrency, Autonomous Vehicles, Drones, Medical Advances\n"
            "   - Cyber:\n"
            "     - Data Exfiltration, Contagious Malware, Cloud Outage, Financial Theft, Distributed Denial of Service, Internet of Things, Industrial Control Systems, Internet Failure\n"
            "   - Critical Infrastructure:\n"
            "     - Power, Transport, Telecommunications, Satellite Systems, Water & Waste, Fuel, Gas\n"
            "   - Industrial Accident:\n"
            "     - Fire, Explosion, Pollution, Structural Failure, Nuclear\n\n"
            "4. Environmental:\n"
            "   - Extreme Weather:\n"
            "     - Flood, Tropical Windstorm, Temperate Windstorm, Drought, Freeze, Heatwave, Wildfire\n"
            "   - Geophysical:\n"
            "     - Earthquake, Volcanic Eruption, Tsunami\n"
            "   - Space:\n"
            "     - Solar Storm, Astronomical Impact Event\n"
            "   - Climate Change:\n"
            "     - Physical, Liability, Transition, Increase in Extreme Weather, Sea Level Rise, Ocean Acidification, Lower Carbon Economy\n"
            "   - Environmental Degradation:\n"
            "     - Waste & Pollution, Biodiversity Loss, Ecosystem Collapse, Deforestation, Soil Degradation\n"
            "   - Natural Resource Deficiency:\n"
            "     - Fossil Fuels, Biogeochemicals, Raw Materials, Water\n"
            "   - Food Security:\n"
            "     - Animal Epidemic, Plant Epidemic, Famine\n\n"
            "5. Social:\n"
            "   - Socioeconomic Trends:\n"
            "     - Ageing Population, Gender Imbalance, Wealth Inequality, Poor Educational Standards, Migration\n"
            "   - Human Capital:\n"
            "     - Failure to Attract Talent, Gender & Diversity, Labour Disputes & Strikes, Loss of Key Personnel, Employee Misconduct\n"
            "   - Brand Perception:\n"
            "     - Fake News, Negative Media Coverage, Key Influencer Disruption, Negative Customer Experience\n"
            "   - Sustainable Living:\n"
            "     - Consumer Activism, Sustainable Purchasing, Supply Chain Provenance, Diet\n"
            "   - Health Trends:\n"
            "     - Obesity, Longevity, Antimicrobial Resistance, Medical Breakthroughs, Healthcare, Social Care\n"
            "   - Infectious Disease:\n"
            "     - Influenza Pandemics, Coronavirus-like Epidemics, Viral Hemorrhagic Fevers, Preventable Disease Outbreaks, Unknown Emergent Diseases\n\n"
            "6. Governance:\n"
            "   - Non-Compliance:\n"
            "     - Emerging Regulation, Internal Corruption & Fraud, Negligence, Revised Accounting Standards, Occupational Health & Safety\n"
            "   - Litigation:\n"
            "     - Private Lawsuit, Mass Tort, Class Action\n"
            "   - Strategic Performance:\n"
            "     - Divestitures, Joint Ventures, Mergers & Acquisitions, Restructuring, Poor Investment\n"
            "   - Management Performance:\n"
            "     - Executive Mismanagement, Ineffective Board, Management Execution Failure\n"
            "   - Business Model Deficiencies:\n"
            "     - Technology, Customer Preference Change\n"
            "   - Pension Management:\n"
            "     - Contribution Management, Fund Management\n"
            "   - Products & Services:\n"
            "     - Product Defect/Failure, Innovation (R&D) Failure\n\n"
            "Return the output as a list of Risk objects in this format:\n"
            "[\n"
            "  {\"class_name\": \"Geopolitical\", \"families\": [\"Corruption & Crime\", \"Political Violence\"]},\n"
            "  {\"class_name\": \"Social\", \"families\": [\"Socioeconomic Trends\"]}\n"
            "]"
        )

        class RiskList(BaseModel):
            risks: List[Risk]

        try:
            response = self.gpt_service.call_gpt_with_schema(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": risk_prompt},
                ],
                schema=RiskList
            )

            event.risk_categories = response.risks
        except Exception as e:
            print(f"Error assigning risk categories: {e}")
            event.risk_categories = []

        return event

    def assign_location(self, event: Event) -> Event:
        """
        Assign a location to an event based on its title and description.
        """

        system_prompt = (
            "You are an expert supply chain analyst. Your task is to determine the most relevant location "
            "for an event based on its description and title, focusing on its impact on supply chains. "
            "Consider how and where the event could disrupt supply chain operations.\n\n"
            "Rules:\n"
            "1. Assign a location only if it is clearly relevant to the supply chain impact of the event.\n"
            "   - This could be the location where the event occurs, or where its effects are most significant.\n"
            "2. If the event affects multiple countries or an entire region, use `geographic_scope` to indicate "
            "this broader impact (e.g., 'Global', 'Asia', 'Europe').\n"
            "3. Provide the most relevant level of detail (country, region, city) without being overly specific.\n"
            "4. If no specific location can be determined, set the location to a broad `geographic_scope` (e.g., 'Global').\n\n"
            "Output format:\n"
            "{\n"
            "  \"geographic_scope\": \"<Global or Continent>\",\n"
            "  \"country\": \"<Country>\",\n"
            "  \"region\": \"<Region>\",\n"
            "  \"city\": \"<City>\",\n"
            "  \"coordinates\": [<Latitude>, <Longitude>]\n"
            "}\n"
            "If no specific location is relevant, return:\n"
            "{\n"
            "  \"geographic_scope\": \"Global\",\n"
            "  \"country\": null,\n"
            "  \"region\": null,\n"
            "  \"city\": null,\n"
            "  \"coordinates\": null\n"
            "}\n\n"
            "Examples:\n"
            "1. **Specific Location**:\n"
            "   Event Title: \"China's Tightened Export Controls Impact Apple Supply Chain\"\n"
            "   Event Description: \"Apple's efforts to diversify its supply chain are being hindered by tightened export "
            "   controls imposed by China. The restrictions are affecting manufacturing processes and may lead to delays.\"\n"
            "   Output:\n"
            "   {\n"
            "     \"geographic_scope\": null,\n"
            "     \"country\": \"China\",\n"
            "     \"region\": null,\n"
            "     \"city\": null,\n"
            "     \"coordinates\": [35.8617, 104.1954]\n"
            "   }\n\n"
            "2. **Global Impact**:\n"
            "   Event Title: \"Security Vulnerabilities in DNA Sequencers\"\n"
            "   Event Description: \"Eclypsium, an Argentine cybersecurity firm, has reported that leading DNA sequencing "
            "   devices are running on outdated firmware, making them vulnerable to takeovers and disruptions. "
            "   This could affect clinical research globally.\"\n"
            "   Output:\n"
            "   {\n"
            "     \"geographic_scope\": \"Global\",\n"
            "     \"country\": null,\n"
            "     \"region\": null,\n"
            "     \"city\": null,\n"
            "     \"coordinates\": null\n"
            "   }\n\n"
            "3. **Region-Specific Impact**:\n"
            "   Event Title: \"Floods Disrupt Logistics in Southeast Asia\"\n"
            "   Event Description: \"Severe flooding in Southeast Asia has disrupted major shipping routes, delaying "
            "   goods bound for global markets.\"\n"
            "   Output:\n"
            "   {\n"
            "     \"geographic_scope\": \"Asia\",\n"
            "     \"country\": null,\n"
            "     \"region\": \"Southeast Asia\",\n"
            "     \"city\": null,\n"
            "     \"coordinates\": null\n"
            "   }\n"
        )

        user_prompt = (
            f"Event Title: {event.title}\n"
            f"Event Description: {event.description}\n\n"
            "Determine the most relevant location for this event's impact on supply chains. "
            "Provide the output as a `Location` object in the specified format."
        )

        try:
            response = self.gpt_service.call_gpt_with_schema(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                schema=Location
            )

            event.location = response
        except Exception as e:
            print(f"Error assigning location: {e}")
            event.location = None

        return event
