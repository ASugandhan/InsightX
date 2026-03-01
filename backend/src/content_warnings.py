"""
Content Warnings Module - Detects and warns about out-of-context and restricted requests.
Provides context-specific warning messages to guide users.
"""

import re
from typing import Tuple, List, Dict
from enum import Enum


class WarningCategory(Enum):
    """Categories of content warnings."""
    OUT_OF_CONTEXT = "out_of_context"
    EXPLICIT_CONTENT = "explicit_content"
    RESTRICTED_DOMAIN = "restricted_domain"
    SECURITY_THREAT = "security_threat"
    NO_INTENT = "no_intent"
    UNCLEAR_INTENT = "unclear_intent"


# ============================================================================
# OUT-OF-CONTEXT PATTERNS WITH SPECIFIC CATEGORIES
# ============================================================================
OUT_OF_CONTEXT_PATTERNS = [
    # Programming & Technology - General Knowledge
    (r'\b(what is|define|explain|tell me about)\s+(ai|artificial intelligence|machine learning|deep learning|neural network)\b', "ai_ml"),
    (r'\b(what is|define|explain|tell me about)\s+(python|javascript|java|c\+\+|golang|rust)\b', "programming_languages"),
    (r'\b(what is|define|explain|tell me about)\s+(sql|database|nosql|mongodb|postgresql)\b', "database_technology"),
    (r'\b(how to|tutorial|guide|learn)\s+\w+\s+(programming|coding|development|algorithm)\b', "programming_tutorial"),
    
    # Scientific & Academic
    (r'\b(physics|quantum|relativity|cosmology|thermodynamics)\b', "physics"),
    (r'\b(chemistry|organic|biochemistry|molecular|compound)\b', "chemistry"),
    (r'\b(biology|genetics|dna|evolution|organism)\b', "biology"),
    (r'\b(mathematics|calculus|algebra|geometry|trigonometry)\b', "mathematics"),
    (r'\b(history|historical|ancient|archaeology|civilization)\b', "history"),
    (r'\b(geography|geological|continent|climate|geology)\b', "geography"),
    
    # Current Events & News
    (r'\b(weather|forecast|temperature|climate today)\b', "weather"),
    (r'\b(sports|cricket|football|soccer|basketball|match|tournament)\b', "sports"),
    (r'\b(news|breaking|headline|latest update|current event)\b', "news"),
    (r'\b(politics|political|government|election|politician|parliament)\b', "politics"),
    (r'\b(celebrity|actor|actress|hollywood|bollywood|fame)\b', "celebrities"),
    
    # Lifestyle & Daily Life
    (r'\b(recipe|cooking|cook|prepare|ingredient|dish)\b', "cooking"),
    (r'\b(diet|nutrition|calorie|weight loss|fitness plan)\b', "diet_fitness"),
    (r'\b(exercise|workout|gym|stretching|cardio)\b', "exercise"),
    (r'\b(fashion|clothing|dress|style|outfit)\b', "fashion"),
    
    # Entertainment
    (r'\b(movie|film|cinema|watch|recommend.*movie)\b', "movies"),
    (r'\b(music|song|artist|singer|album|concert)\b', "music"),
    (r'\b(book|novel|author|read|literature)\b', "books"),
    (r'\b(game|gaming|video game|play.*game)\b', "games"),
    (r'\b(tv show|series|episode|binge|watch online)\b', "tv_shows"),
    (r'\b(joke|funny|comedy|meme|laugh)\b', "humor"),
    
    # Opinions & Beliefs
    (r'\b(philosophy|philosophical|ethics|morality)\b', "philosophy"),
    (r'\b(religion|religious|faith|spiritual|worship)\b', "religion"),
    (r'\b(opinion|think|believe|should)\s+\w+\s+(is|are)\b', "opinion_based"),
]

# ============================================================================
# EXPLICIT CONTENT PATTERNS
# ============================================================================
EXPLICIT_PATTERNS = [
    (r'\b(porn|xxx|sex|naked|adult|nsfw|18\+)\b', "adult_content"),
    (r'\+\d{1,3}\s*\d{6,14}', "phone_number"),  # Phone numbers
    (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', "personal_email"),
    (r'\b\d{3}-\d{2}-\d{4}\b', "ssn_pattern"),
]

# ============================================================================
# RESTRICTED DOMAIN PATTERNS
# ============================================================================
RESTRICTED_DOMAIN_PATTERNS = [
    (r'\b(hack|crack|exploit|vulnerability|bypass|jailbreak|break in)\b', "hacking"),
    (r'\b(create.*virus|malware|ransomware|botnet)\b', "malware"),
    (r'\b(password crack|brute force|ddos|dos attack)\b', "cyber_attack"),
    (r'\b(clone card|forge|counterfeit|fake)\b', "fraud"),
    (r'\b(money launder|smuggle|illegal trade|black market)\b', "illegal_activity"),
]

# ============================================================================
# NO INTENT / UNCLEAR INTENT PATTERNS
# ============================================================================
NO_INTENT_PATTERNS = [
    r'^[a-z]$',  # Single character
    r'^\W+$',  # Only special characters
    r'^(hmm|umm|err|uh|ok|yes|no|yep|nope)$',  # Non-specific responses
    r'^(\.+|!+|\?+)$',  # Only punctuation
]

UNCLEAR_INTENT_PATTERNS = [
    (r'^(it|this|that|there|what|huh|something)\s*$', "vague_pronoun"),
    (r'^(bye|goodbye|thanks|thank you|hello|hi|hey|yo)\s*$', "greeting_only"),
]

# ============================================================================
# WARNING MESSAGES - SPECIFIC AND PERSONALIZED
# ============================================================================
WARNING_MESSAGES = {
    WarningCategory.OUT_OF_CONTEXT: {
        # AI & Machine Learning
        "ai_ml": (
            "⚠️ Out of Scope - AI/ML Topic: Your question is about Artificial Intelligence or Machine Learning, which is outside my domain.\n"
            "I'm specialized in UPI transaction analytics, not general AI/ML concepts.\n\n"
            "💡 What I CAN help with:\n"
            "  • Analyze fraud patterns using transaction ML features\n"
            "  • Predict failure rates by device type or user segment\n"
            "  • Detect anomalies in transaction behavior\n"
            "  • Identify high-risk transaction patterns\n\n"
            "❓ Try asking: 'What fraud patterns exist in transactions over Rs 10,000?' or 'Which user segments have highest failure rates?'"
        ),
        
        # Programming Languages
        "programming_languages": (
            "⚠️ Out of Scope - Programming Topic: Your question is about programming languages, which I cannot assist with.\n"
            "I focus on UPI transaction data analysis, not software development.\n\n"
            "💡 What I CAN help with:\n"
            "  • Analyze transaction patterns by device type (iOS/Android/Feature Phone)\n"
            "  • Compare success rates across different UPI apps\n"
            "  • Identify network-related transaction issues\n"
            "  • Analyze transaction latency by network type\n\n"
            "❓ Try asking: 'Which UPI app has the best success rate?' or 'Do Android users have different failure patterns than iOS users?'"
        ),
        
        # Database Technology
        "database_technology": (
            "⚠️ Out of Scope - Database/Tech Topic: Your question is about database technology, which is outside my scope.\n"
            "I specialize in querying and analyzing UPI transaction data, not database concepts.\n\n"
            "💡 What I CAN help with:\n"
            "  • Query transaction data by various filters\n"
            "  • Analyze data by merchant categories\n"
            "  • Compare transactions across different states\n"
            "  • Find patterns in transaction timing and amounts\n\n"
            "❓ Try asking: 'Show me transactions by merchant category' or 'Which states have the highest fraud rates?'"
        ),
        
        # Programming Tutorials
        "programming_tutorial": (
            "⚠️ Out of Scope - Programming Tutorial: You're looking for coding help, but I'm a UPI analytics specialist.\n"
            "I cannot provide programming tutorials or development guidance.\n\n"
            "💡 What I CAN help with:\n"
            "  • Analyze UPI transaction patterns and trends\n"
            "  • Generate reports on transaction success/failure\n"
            "  • Identify peak transaction hours and patterns\n"
            "  • Calculate fraud rates by user segment\n\n"
            "❓ Try asking: 'What are the peak transaction hours?' or 'Show me fraud trends by age group?'"
        ),
        
        # Physics
        "physics": (
            "⚠️ Out of Scope - Physics: Your question is about physics, which is completely outside my domain.\n"
            "I'm designed for UPI financial transaction analysis only.\n\n"
            "💡 What I CAN help with:\n"
            "  • Analyze financial transaction patterns\n"
            "  • Study transaction behavior by user demographics\n"
            "  • Identify payment success/failure trends\n"
            "  • Discover fraud patterns and anomalies\n\n"
            "❓ Try asking: 'What causes transaction failures?' or 'Show me fraud trends by demographics?'"
        ),
        
        # Chemistry
        "chemistry": (
            "⚠️ Out of Scope - Chemistry: Your question is about chemistry, which is outside my scope.\n"
            "I exclusively analyze UPI transaction data - not chemistry or scientific topics.\n\n"
            "💡 What I CAN help with:\n"
            "  • Breakdown transactions by type (P2P, P2M)\n"
            "  • Analyze transaction composition and patterns\n"
            "  • Study failure reasons and their frequency\n"
            "  • Compare transaction metrics across segments\n\n"
            "❓ Try asking: 'What's the breakdown of P2P vs P2M transactions?' or 'Which failure reasons are most common?'"
        ),
        
        # Biology
        "biology": (
            "⚠️ Out of Scope - Biology: Your question is about biology, which I cannot help with.\n"
            "I specialize in financial transaction analytics, not biological sciences.\n\n"
            "💡 What I CAN help with:\n"
            "  • Analyze transaction patterns across user groups\n"
            "  • Study behavior by age group demographics\n"
            "  • Identify transaction growth trends\n"
            "  • Find patterns in user payment behavior\n\n"
            "❓ Try asking: 'Which age group has the highest transaction volume?' or 'Show me fraud rates by age?'"
        ),
        
        # Mathematics
        "mathematics": (
            "⚠️ Out of Scope - Mathematics: Your question is about math concepts, which is outside my scope.\n"
            "While I use analytics, I'm specialized in transaction data, not math education.\n\n"
            "💡 What I CAN help with:\n"
            "  • Calculate transaction statistics (averages, rates, percentages)\n"
            "  • Analyze numerical trends in payment data\n"
            "  • Find correlations in transaction patterns\n"
            "  • Generate quantitative insights from data\n\n"
            "❓ Try asking: 'What's the average transaction amount?' or 'Calculate the failure rate by device type?'"
        ),
        
        # History
        "history": (
            "⚠️ Out of Scope - History: Your question is about history, which I cannot assist with.\n"
            "I focus on analyzing current UPI transaction data, not historical events.\n\n"
            "💡 What I CAN help with:\n"
            "  • Analyze UPI transaction trends over time\n"
            "  • Compare weekday vs weekend patterns\n"
            "  • Track transaction growth trends\n"
            "  • Identify seasonal patterns in transactions\n\n"
            "❓ Try asking: 'Show me transaction trends over time' or 'How do weekends differ from weekdays?'"
        ),
        
        # Geography
        "geography": (
            "⚠️ Out of Scope - Geography: Your question is about geography, which is outside my domain.\n"
            "I analyze UPI transactions, not geographical concepts.\n\n"
            "💡 What I CAN help with:\n"
            "  • Analyze transactions by state location\n"
            "  • Compare transaction metrics across regions\n"
            "  • Identify state-wise patterns and trends\n"
            "  • Find regional differences in transaction behavior\n\n"
            "❓ Try asking: 'Which state has the most transactions?' or 'Show me fraud rates by state?'"
        ),
        
        # Weather
        "weather": (
            "⚠️ Out of Scope - Weather: Your question is about weather, which I cannot help with.\n"
            "I'm dedicated to UPI transaction analytics, not meteorology.\n\n"
            "💡 What I CAN help with:\n"
            "  • Analyze transactions by time of day\n"
            "  • Study weekend vs weekday patterns\n"
            "  • Identify peak transaction periods\n"
            "  • Analyze seasonal transaction trends\n\n"
            "❓ Try asking: 'Show me peak transaction hours' or 'How do transactions differ on weekends?'"
        ),
        
        # Sports
        "sports": (
            "⚠️ Out of Scope - Sports: Your question is about sports, which I cannot assist with.\n"
            "I specialize in UPI financial transactions, not sports.\n\n"
            "💡 What I CAN help with:\n"
            "  • Analyze transaction patterns and performance metrics\n"
            "  • Compare success rates across categories\n"
            "  • Identify top-performing segments\n"
            "  • Track transaction volume trends\n\n"
            "❓ Try asking: 'Which merchant category has the best success rate?' or 'Show me top transaction categories?'"
        ),
        
        # News
        "news": (
            "⚠️ Out of Scope - News/Current Events: Your question is about news, which is outside my scope.\n"
            "I don't cover current events; I analyze UPI transaction data.\n\n"
            "💡 What I CAN help with:\n"
            "  • Analyze historical transaction trends\n"
            "  • Identify patterns in transaction behavior\n"
            "  • Generate reports on transaction metrics\n"
            "  • Discover insights in payment patterns\n\n"
            "❓ Try asking: 'Show me transaction trends over the past period' or 'What patterns exist in the data?'"
        ),
        
        # Politics
        "politics": (
            "⚠️ Out of Scope - Politics: Your question is about politics, which I cannot discuss.\n"
            "I focus on financial transaction analytics, not political topics.\n\n"
            "💡 What I CAN help with:\n"
            "  • Analyze digital payment trends\n"
            "  • Study transaction behavior across regions\n"
            "  • Identify payment patterns by demographics\n"
            "  • Generate financial insights from data\n\n"
            "❓ Try asking: 'Show me transaction distribution by state' or 'Which demographics use UPI most?'"
        ),
        
        # Celebrities
        "celebrities": (
            "⚠️ Out of Scope - Celebrities: Your question is about celebrities, which is outside my domain.\n"
            "I analyze transaction data, not entertainment industry topics.\n\n"
            "💡 What I CAN help with:\n"
            "  • Analyze transaction patterns across users\n"
            "  • Study payment behavior trends\n"
            "  • Identify popular merchant categories\n"
            "  • Generate insights from transaction metrics\n\n"
            "❓ Try asking: 'Which merchant category has the most transactions?' or 'Show me user behavior patterns?'"
        ),
        
        # Cooking
        "cooking": (
            "⚠️ Out of Scope - Cooking: Your question is about cooking/recipes, which I cannot help with.\n"
            "I specialize in UPI transaction analytics, not culinary guidance.\n\n"
            "💡 What I CAN help with:\n"
            "  • Analyze transactions at food merchant categories\n"
            "  • Study spending patterns on merchants\n"
            "  • Identify popular transaction types\n"
            "  • Analyze transaction amounts and frequencies\n\n"
            "❓ Try asking: 'Show me transaction patterns for food merchants' or 'Which merchant category has highest volume?'"
        ),
        
        # Diet & Fitness
        "diet_fitness": (
            "⚠️ Out of Scope - Diet/Fitness: Your question is about diet or fitness, which is outside my scope.\n"
            "I analyze transaction data, not health or fitness topics.\n\n"
            "💡 What I CAN help with:\n"
            "  • Analyze spending on health-related merchants\n"
            "  • Study transaction patterns for wellness\n"
            "  • Identify health merchant transaction trends\n"
            "  • Compare spending across user segments\n\n"
            "❓ Try asking: 'Show me transactions at health merchants' or 'Analyze spending patterns by category?'"
        ),
        
        # Exercise
        "exercise": (
            "⚠️ Out of Scope - Exercise: Your question is about exercise, which I cannot assist with.\n"
            "I focus on UPI transaction analysis, not fitness guidance.\n\n"
            "💡 What I CAN help with:\n"
            "  • Analyze transactions at fitness merchants\n"
            "  • Study spending patterns on gym/sports\n"
            "  • Identify transaction trends for wellness merchants\n"
            "  • Compare user spending by category\n\n"
            "❓ Try asking: 'Show me transactions at gym merchants' or 'Analyze wellness spending patterns?'"
        ),
        
        # Fashion
        "fashion": (
            "⚠️ Out of Scope - Fashion: Your question is about fashion/clothing, which is outside my domain.\n"
            "I specialize in UPI transaction data analysis, not fashion advice.\n\n"
            "💡 What I CAN help with:\n"
            "  • Analyze transactions at fashion merchants\n"
            "  • Study spending patterns on clothing\n"
            "  • Identify popular fashion merchant transactions\n"
            "  • Compare transaction amounts across merchants\n\n"
            "❓ Try asking: 'Show me transactions at fashion merchants' or 'Analyze retail spending patterns?'"
        ),
        
        # Movies
        "movies": (
            "⚠️ Out of Scope - Movies: Your question is about movies, which I cannot help with.\n"
            "I'm specialized in UPI transaction analytics, not entertainment recommendations.\n\n"
            "💡 What I CAN help with:\n"
            "  • Analyze transactions at movie/entertainment merchants\n"
            "  • Study spending patterns on entertainment\n"
            "  • Identify entertainment merchant trends\n"
            "  • Compare transaction frequency by category\n\n"
            "❓ Try asking: 'Show me entertainment merchant transactions' or 'Analyze spending on entertainment?'"
        ),
        
        # Music
        "music": (
            "⚠️ Out of Scope - Music: Your question is about music, which is outside my scope.\n"
            "I analyze financial transactions, not music topics.\n\n"
            "💡 What I CAN help with:\n"
            "  • Analyze transactions at music/streaming services\n"
            "  • Study subscription payment patterns\n"
            "  • Identify music merchant transaction trends\n"
            "  • Compare spending on entertainment\n\n"
            "❓ Try asking: 'Show me transactions at music merchants' or 'Analyze entertainment spending?'"
        ),
        
        # Books
        "books": (
            "⚠️ Out of Scope - Books/Literature: Your question is about books, which I cannot assist with.\n"
            "I specialize in UPI transaction analysis, not literature or reading.\n\n"
            "💡 What I CAN help with:\n"
            "  • Analyze transactions at book/education merchants\n"
            "  • Study spending patterns on learning\n"
            "  • Identify education merchant trends\n"
            "  • Compare transaction amounts by merchant category\n\n"
            "❓ Try asking: 'Show me education merchant transactions' or 'Analyze learning spend patterns?'"
        ),
        
        # Games
        "games": (
            "⚠️ Out of Scope - Gaming: Your question is about gaming, which is outside my domain.\n"
            "I focus on UPI transaction analytics, not gaming recommendations.\n\n"
            "💡 What I CAN help with:\n"
            "  • Analyze transactions at gaming/entertainment merchants\n"
            "  • Study spending patterns on entertainment\n"
            "  • Identify gaming merchant transaction trends\n"
            "  • Compare user spending across categories\n\n"
            "❓ Try asking: 'Show me gaming merchant transactions' or 'Analyze entertainment spending trends?'"
        ),
        
        # TV Shows
        "tv_shows": (
            "⚠️ Out of Scope - TV Shows: Your question is about TV shows, which I cannot help with.\n"
            "I specialize in UPI transaction data, not entertainment content.\n\n"
            "💡 What I CAN help with:\n"
            "  • Analyze transactions at OTT/streaming platforms\n"
            "  • Study entertainment subscription patterns\n"
            "  • Identify streaming service transaction trends\n"
            "  • Compare entertainment spending by user segment\n\n"
            "❓ Try asking: 'Show me streaming service transactions' or 'Analyze OTT spending patterns?'"
        ),
        
        # Humor
        "humor": (
            "⚠️ Out of Scope - Humor: Your question is looking for humor, which is outside my purpose.\n"
            "I'm dedicated to serious UPI transaction analytics, not entertainment.\n\n"
            "💡 What I CAN help with:\n"
            "  • Analyze transaction data and patterns\n"
            "  • Generate interesting insights from data\n"
            "  • Identify surprising trends in payments\n"
            "  • Create fascinating reports on transactions\n\n"
            "❓ Try asking: 'Show me surprising patterns in the data' or 'What's the most interesting transaction trend?'"
        ),
        
        # Philosophy
        "philosophy": (
            "⚠️ Out of Scope - Philosophy: Your question is about philosophy, which is outside my scope.\n"
            "I analyze quantitative transaction data, not philosophical concepts.\n\n"
            "💡 What I CAN help with:\n"
            "  • Analyze transaction behavior and patterns\n"
            "  • Study user transaction decision patterns\n"
            "  • Identify trends in payment choices\n"
            "  • Generate data-driven insights\n\n"
            "❓ Try asking: 'What patterns exist in user transaction behavior?' or 'Show me spending trends?'"
        ),
        
        # Religion
        "religion": (
            "⚠️ Out of Scope - Religion: Your question is about religion, which I cannot discuss.\n"
            "I focus on UPI transaction analytics, not religious topics.\n\n"
            "💡 What I CAN help with:\n"
            "  • Analyze transactions across all user segments\n"
            "  • Study payment patterns by demographics\n"
            "  • Identify transaction trends universally\n"
            "  • Generate inclusive financial insights\n\n"
            "❓ Try asking: 'Show me transaction patterns by demographics' or 'Analyze payments across segments?'"
        ),
        
        # Opinion-based
        "opinion_based": (
            "⚠️ Out of Scope - Opinion Question: Your question asks for opinions or subjective views.\n"
            "I'm data-driven and only provide fact-based analysis, not opinions.\n\n"
            "💡 What I CAN help with:\n"
            "  • Analyze actual transaction data objectively\n"
            "  • Generate fact-based insights\n"
            "  • Identify patterns in data\n"
            "  • Provide data-driven conclusions\n\n"
            "❓ Try asking: 'What does the data show about transaction success rates?' or 'Analyze fraud patterns objectively?'"
        ),
    },
    WarningCategory.EXPLICIT_CONTENT: {
        "adult_content": (
            "⚠️ Inappropriate Content: Your query contains adult or explicit content which I cannot process. "
            "Please refrain from such requests and focus on legitimate UPI transaction inquiries."
        ),
        "phone_number": (
            "⚠️ Privacy Alert: Your message appears to contain a phone number. "
            "Please do not share personal contact information. I analyze transaction patterns, not personal data."
        ),
        "personal_email": (
            "⚠️ Privacy Alert: Your message contains an email address. "
            "For your security, avoid sharing personal contact details. Focus on transaction data analysis instead."
        ),
        "ssn_pattern": (
            "⚠️ Security Alert: Your message pattern resembles sensitive identification numbers. "
            "Never share such information. I only work with transaction data."
        ),
    },
    WarningCategory.RESTRICTED_DOMAIN: {
        "hacking": (
            "⚠️ Security Alert: Your query appears to involve hacking or unauthorized access. "
            "I cannot provide assistance with such activities. All requests must be for legitimate, authorized analytics only."
        ),
        "malware": (
            "⚠️ Security Alert: Your query involves malware or harmful software. "
            "I cannot and will not provide guidance on creating malicious software."
        ),
        "cyber_attack": (
            "⚠️ Security Alert: Your request appears to involve cyber attacks. "
            "Such activities are illegal and unethical. I cannot assist with them."
        ),
        "fraud": (
            "⚠️ Legal Alert: Your query appears to involve fraudulent activities. "
            "I cannot provide assistance with illegal activities. Only legitimate financial analysis is supported."
        ),
        "illegal_activity": (
            "⚠️ Legal Alert: Your request involves illegal activities. "
            "I'm designed for legitimate business and analytical purposes only."
        ),
    },
    WarningCategory.NO_INTENT: {
        "default": (
            "⚠️ No Clear Intent: Your message doesn't contain a clear question or intent. "
            "Please provide a specific question about UPI transactions, such as: "
            "'What is the fraud rate by device type?' or 'Show me failure trends over time.'"
        ),
    },
    WarningCategory.UNCLEAR_INTENT: {
        "vague_pronoun": (
            "⚠️ Unclear Question: Your question uses vague references without context. "
            "Please ask a specific question, for example: "
            "'What is the failure rate for transactions over Rs 5000?' or 'Which age group has the highest fraud rate?'"
        ),
        "greeting_only": (
            "👋 Hello! Welcome to Nexus - Your UPI Transaction Analytics Assistant!\n\n"
            "What would you like to know about your UPI transactions? 🤔\n\n"
            "Here are some insights I can provide:\n"
            "  📊 Transaction Trends: Patterns over time, peak hours, seasonal changes\n"
            "  🛡️ Fraud Analysis: Fraud rates by device, age group, merchant category\n"
            "  ⚙️ Performance Metrics: Success rates, failure analysis, latency issues\n"
            "  👥 User Segments: Behavior by device type, age group, financial patterns\n"
            "  🏪 Merchant Insights: Category performance, popular merchants, spending patterns\n"
            "  🌍 Geographic Analysis: State-wise trends, regional patterns\n\n"
            "💡 You can ask:\n"
            "  • 'What is the fraud rate by device type?'\n"
            "  • 'Show me the most popular merchant categories'\n"
            "  • 'Which age group has the highest failure rate?'\n"
            "  • 'Analyze transaction patterns for P2P vs P2M'\n"
            "  • 'What are the peak transaction hours?'\n\n"
            "What insights would you like to discover? 🔍"
        ),
    },
}


class ContentWarningDetector:
    """Detects content warnings and generates context-specific warning messages."""

    def __init__(self):
        self.out_of_context_patterns = [
            (re.compile(p, re.IGNORECASE), cat) for p, cat in OUT_OF_CONTEXT_PATTERNS
        ]
        self.explicit_patterns = [
            (re.compile(p, re.IGNORECASE), cat) for p, cat in EXPLICIT_PATTERNS
        ]
        self.restricted_domain_patterns = [
            (re.compile(p, re.IGNORECASE), cat) for p, cat in RESTRICTED_DOMAIN_PATTERNS
        ]
        self.no_intent_patterns = [re.compile(p, re.IGNORECASE) for p in NO_INTENT_PATTERNS]
        self.unclear_intent_patterns = [
            (re.compile(p, re.IGNORECASE), cat) for p, cat in UNCLEAR_INTENT_PATTERNS
        ]

    def detect(self, question: str) -> Tuple[bool, List[Dict]]:
        """
        Detect content warnings in a question.
        
        Returns:
            (has_warnings, warnings_list)
            where warnings_list contains dicts with:
            - category: WarningCategory
            - type: specific warning type
            - message: warning message to show user
            - severity: 'info', 'warning', or 'critical'
        """
        warnings = []

        # 1. Check for no intent
        if self._check_no_intent(question):
            warnings.append({
                "category": WarningCategory.NO_INTENT.value,
                "type": "default",
                "message": WARNING_MESSAGES[WarningCategory.NO_INTENT]["default"],
                "severity": "warning"
            })
            return True, warnings

        # 2. Check for unclear intent
        unclear_warning = self._check_unclear_intent(question)
        if unclear_warning:
            warnings.append(unclear_warning)
            return True, warnings

        # 3. Check for restricted domain (highest severity)
        restricted_warning = self._check_restricted_domain(question)
        if restricted_warning:
            warnings.append(restricted_warning)
            return True, warnings

        # 4. Check for explicit content
        explicit_warning = self._check_explicit_content(question)
        if explicit_warning:
            warnings.append(explicit_warning)
            return True, warnings

        # 5. Check for out-of-context
        out_of_context_warnings = self._check_out_of_context(question)
        if out_of_context_warnings:
            warnings.extend(out_of_context_warnings)
            return True, warnings

        return False, warnings

    def _check_no_intent(self, question: str) -> bool:
        """Check if question has no clear intent."""
        q = question.strip()
        for pattern in self.no_intent_patterns:
            if pattern.match(q):
                return True
        return False

    def _check_unclear_intent(self, question: str) -> Dict:
        """Check if question has unclear intent."""
        q = question.strip().lower()
        for pattern, category in self.unclear_intent_patterns:
            if pattern.match(q):
                return {
                    "category": WarningCategory.UNCLEAR_INTENT.value,
                    "type": category,
                    "message": WARNING_MESSAGES[WarningCategory.UNCLEAR_INTENT][category],
                    "severity": "info"
                }
        return None

    def _check_restricted_domain(self, question: str) -> Dict:
        """Check if question involves restricted/illegal activities."""
        for pattern, category in self.restricted_domain_patterns:
            if pattern.search(question):
                return {
                    "category": WarningCategory.RESTRICTED_DOMAIN.value,
                    "type": category,
                    "message": WARNING_MESSAGES[WarningCategory.RESTRICTED_DOMAIN][category],
                    "severity": "critical"
                }
        return None

    def _check_explicit_content(self, question: str) -> Dict:
        """Check if question contains explicit content."""
        for pattern, category in self.explicit_patterns:
            if pattern.search(question):
                return {
                    "category": WarningCategory.EXPLICIT_CONTENT.value,
                    "type": category,
                    "message": WARNING_MESSAGES[WarningCategory.EXPLICIT_CONTENT][category],
                    "severity": "critical"
                }
        return None

    def _check_out_of_context(self, question: str) -> List[Dict]:
        """Check for out-of-context questions with specific category detection."""
        warnings = []
        detected_categories = set()
        
        for pattern, category in self.out_of_context_patterns:
            match = pattern.search(question)
            if match and category not in detected_categories:
                # Get the specific warning message for this category
                msg = WARNING_MESSAGES[WarningCategory.OUT_OF_CONTEXT].get(
                    category,
                    "⚠️ Out of Scope: Your question appears to be outside the domain of UPI transaction analytics. "
                    "Please ask questions related to transaction analysis instead."
                )
                
                warnings.append({
                    "category": WarningCategory.OUT_OF_CONTEXT.value,
                    "type": category,
                    "message": msg,
                    "severity": "warning",
                    "matched_keyword": match.group(0) if match else None
                })
                detected_categories.add(category)
                # Return on first match to avoid multiple warnings
                return warnings
        
        return warnings

    def should_block_request(self, warnings: List[Dict]) -> bool:
        """
        Determine if request should be blocked based on warnings.
        
        Block if:
        - Any critical severity warnings exist (restricted domain, explicit content)
        """
        for warning in warnings:
            if warning.get("severity") == "critical":
                return True
        return False

    def format_warnings_for_response(self, warnings: List[Dict]) -> str:
        """Format warnings as a user-friendly string with context-specific suggestions."""
        if not warnings:
            return ""
        
        warning_text = ""
        for warning in warnings:
            warning_text += warning["message"] + "\n\n"
        
        return warning_text.strip()

    def get_category_examples(self, category: str) -> List[str]:
        """Get relevant example questions for a specific warning category."""
        examples_by_category = {
            "ai_ml": [
                "What fraud patterns exist in transactions over Rs 10,000?",
                "Which user segments have the highest failure rates?",
                "Can you predict failure patterns by device type?",
                "Analyze anomalies in high-value transactions"
            ],
            "programming_languages": [
                "Which UPI app has the best success rate?",
                "Do Android users have different failure patterns than iOS users?",
                "Show me transaction differences by device type",
                "Analyze latency patterns across network types"
            ],
            "database_technology": [
                "Show me transactions by merchant category",
                "Which states have the highest fraud rates?",
                "Compare transactions by transaction type",
                "Analyze transactions by sender age group"
            ],
            "weather": [
                "Show me peak transaction hours",
                "How do transactions differ on weekends?",
                "What are the transaction patterns by hour of day?",
                "Analyze daily transaction trends"
            ],
            "cooking": [
                "Show me transaction patterns for food merchants",
                "Which merchant category has highest transaction volume?",
                "Analyze spending patterns by merchant type",
                "Compare transaction amounts across categories"
            ],
            "movies": [
                "Show me entertainment merchant transactions",
                "Analyze OTT platform transaction patterns",
                "What's the spending trend on streaming services?",
                "Compare entertainment spending by user segment"
            ],
            "default": [
                "What is the fraud rate by device type?",
                "Show me transaction success rates by age group",
                "Which merchant category is most popular?",
                "Analyze failure patterns by transaction type"
            ]
        }
        
        return examples_by_category.get(category, examples_by_category["default"])

