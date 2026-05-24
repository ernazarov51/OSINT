from .github import collect_github
from .gitlab import collect_gitlab
from .linkedin import collect_linkedin
from .instagram import collect_instagram
from .twitter import collect_twitter
from .tiktok import collect_tiktok
from .youtube import collect_youtube
from .telegram import collect_telegram
from .pinterest import collect_pinterest
from .steam import collect_steam
from .hackernews import collect_hackernews

ALL_COLLECTORS = [
    collect_github,
    collect_gitlab,
    collect_linkedin,
    collect_instagram,
    collect_twitter,
    collect_tiktok,
    collect_youtube,
    collect_telegram,
    collect_pinterest,
    collect_steam,
    collect_hackernews,
]
