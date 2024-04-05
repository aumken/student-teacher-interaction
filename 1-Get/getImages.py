import os

from dotenv import load_dotenv
from requests import Session

env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path=env_path)

# Constants
API_KEY = os.environ.get("FLICKR_API_KEY")
BASE_URL = "https://www.flickr.com/services/rest"
PER_PAGE = 5
BASE_DIR = "a_files/images"
MIN_UPLOAD_DATE = 1704067200

# Ensure the base directory exists
os.makedirs(BASE_DIR, exist_ok=True)

# Tags array remains the same
tags = [
    # Nature
    "mountains",
    "forests",
    "rivers",
    "lakes",
    "oceans",
    "beaches",
    "sunsets",
    "sunrises",
    "flowers",
    "trees",
    "wildlife",
    "deserts",
    "waterfalls",
    "snow",
    "ice",
    "storms",
    "rainbows",
    # Cities and Urban
    "skyscrapers",
    "streets",
    "bridges",
    "nightscapes",
    "city parks",
    "urban art",
    "marketplaces",
    "historical buildings",
    "modern architecture",
    "subways",
    "cafes",
    "rooftops",
    # People and Daily Life
    "portraits",
    "street photography",
    "festivals",
    "markets",
    "sports events",
    "concerts",
    "weddings",
    "dances",
    "family gatherings",
    "school events",
    "workshops",
    # Technology and Industry
    "machinery",
    "factories",
    "construction",
    "robots",
    "electronics",
    "cars",
    "trains",
    "airplanes",
    "space",
    "energy",
    "computers",
    "smartphones",
    # Art and Culture
    "paintings",
    "sculptures",
    "installations",
    "museums",
    "theaters",
    "literature",
    "music",
    "dance",
    "fashion",
    "design",
    "cinema",
    # Sports and Activities
    "soccer",
    "basketball",
    "tennis",
    "swimming",
    "running",
    "cycling",
    "hiking",
    "skiing",
    "snowboarding",
    "surfing",
    "skateboarding",
    "yoga",
    # Animals and Pets
    "cats",
    "dogs",
    "horses",
    "birds",
    "fish",
    "reptiles",
    "insects",
    "wild animals",
    "zoo animals",
    # Food and Drinks
    "fruits",
    "vegetables",
    "desserts",
    "meals",
    "beverages",
    "cocktails",
    "baking",
    "cooking",
    # Travel and Adventure
    "landscapes",
    "seascapes",
    "adventure sports",
    "camping",
    "road trips",
    "cruises",
    "historical sites",
    # Miscellaneous
    "abstract",
    "minimalism",
    "surrealism",
    "macro",
    "night photography",
    "bokeh",
    "black and white",
    "colorful",
    "patterns",
    "textures",
    "shadows",
    "light",
    "reflections",
    "symmetry",
    "aerial views",
    # More to reach over 300
    "gardens",
    "parks",
    "forestry",
    "agriculture",
    "rural life",
    "urban decay",
    "industrial landscapes",
    "digital art",
    "graphic design",
    "typography",
    "calligraphy",
    "street art",
    "graffiti",
    "pop culture",
    "mythology",
    "fantasy",
    "science fiction",
    "historical reenactment",
    "reenactment",
    "cosplay",
    "board games",
    "video games",
    "anime",
    "manga",
    "comics",
    "novels",
    "poetry",
    "classical music",
    "rock music",
    "pop music",
    "jazz music",
    "folk music",
    "world music",
    "cinematography",
    "documentaries",
    "short films",
    "feature films",
    "animation",
    "claymation",
    "puppetry",
    "crafts",
    "woodworking",
    "metalworking",
    "pottery",
    "knitting",
    "sewing",
    "embroidery",
    "beading",
    "jewelry making",
    "quilting",
    "scrapbooking",
    "calligraphy",
    "origami",
    "paper crafts",
    "candle making",
    "soap making",
    "perfumery",
    "floral design",
    "interior design",
    "landscape design",
    "architectural design",
    "industrial design",
    "fashion design",
    "graphic design",
    "web design",
    "user interface design",
    "user experience design",
    "game design",
    "motion graphics",
    "3D modeling",
    "animation",
    "visual effects",
    "photography",
    "cinematography",
    "film production",
    "video editing",
    "sound design",
    "music production",
    "live streaming",
    "podcasting",
    "blogging",
    "vlogging",
    "social media",
    "digital marketing",
    "SEO",
    "web development",
    "app development",
    "software engineering",
    "networking",
    "cybersecurity",
    "artificial intelligence",
    "machine learning",
    "data science",
    "big data",
    "cloud computing",
    "quantum computing",
    "virtual reality",
    "augmented reality",
    "mixed reality",
    "blockchain",
    "cryptocurrency",
    "fintech",
]

# Use a session for network requests
with Session() as session:
    for tag in tags:
        tag_dir = os.path.join(BASE_DIR, tag)
        os.makedirs(tag_dir, exist_ok=True)

        # Loop through the pages (assuming 1 page for now, adjust as needed)
        for page in range(1, 2):  # Change 2 to `pages + 1` if `pages` variable is used
            params = {
                "method": "flickr.photos.search",
                "api_key": API_KEY,
                "tags": tag,
                "format": "json",
                "nojsoncallback": 1,
                "per_page": PER_PAGE,
                "page": page,
                "min_upload_date": MIN_UPLOAD_DATE,
            }

            try:
                response = session.get(BASE_URL, params=params)
                response.raise_for_status()  # Raises an error for bad responses
                photos = response.json()["photos"]["photo"]

                for photo in photos:
                    photo_url = f'https://live.staticflickr.com/{photo["server"]}/{photo["id"]}_{photo["secret"]}_b.jpg'
                    photo_data = session.get(photo_url).content
                    with open(
                        os.path.join(tag_dir, f'{photo["id"]}.jpg'), "wb"
                    ) as handler:
                        handler.write(photo_data)
            except Exception as e:
                print(f"An error occurred: {e}")
