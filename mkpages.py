#!/usr/bin/env python3
"""Generate content/pages.json for the archive.

One-shot generator: the copy below was lifted verbatim from the Squarespace
site before it was retired. Re-running this OVERWRITES content/pages.json, so
once the archive has been hand-edited, edit pages.json directly instead.
"""
import json
from pathlib import Path

OUT = Path(__file__).parent / "content" / "pages.json"

# Image count per page. Everything came off the Squarespace CDN, was capped at
# 1500px on the long side and re-encoded to JPEG q0.82 on the way out — PNGs and
# the two animated GIFs included, so every file is a .jpg. (The two GIFs were
# 19 MB and 18 MB; they are now stills of their first frame.)
COUNT = {
    "story": 5,
    "joopiter-son-of-a-pharaoh": 3,
    "youtube-fashion-beauty-launch": 10,
    "google-pixel-3-grammy-activation": 7,
    "trillectro": 14,
    "youtube-music-rolling-stone-relaunch": 13,
    "youtube-music-megan-thee-stallion": 18,
    "youtube-grammy-party-nyc": 15,
    "youtube-latin-american-creator-summit": 15,
    "youtube-black-creator-summit": 19,
    "google-mixtape": 10,
}

# Near-duplicate frames: the same photograph reappearing further down the page.
DROP = {
    "youtube-music-megan-thee-stallion": [3],
    "youtube-grammy-party-nyc": [4],
    "google-mixtape": [10],
}


def imgs(slug):
    return ["%s-%02d.jpg" % (slug, n + 1) for n in range(COUNT[slug])]


def gallery(slug, cols=3):
    """Every image on the page except the lead and any repeat frames."""
    drop = set(DROP.get(slug, [])) | {COVER.get(slug, 1)}
    vid = VIDEO.get(slug, set())
    items = []
    for n, f in enumerate(imgs(slug), 1):
        if n in drop:
            continue
        items.append({"src": f, "video": f[:-4] + ".mp4"} if n in vid else f)
    return {"type": "gallery", "cols": cols, "items": items}


# A page whose first image makes a poor 4:3 crop can name a different one.
COVER = {"google-mixtape": 3}

# The two animated frames. Squarespace served them as GIFs of 19 MB and 18 MB —
# between them more than the other 128 photographs combined — so they are h.264
# now, 584 KB and 1.3 MB, and the .jpg of their first frame is the poster.
VIDEO = {
    "google-pixel-3-grammy-activation": {2},
    "youtube-black-creator-summit": {15},
}

# Shelved case studies. The copy and the images stay in the repo and in
# pages.json; the page is just not built, not listed on the Projects index,
# and its old Squarespace URL falls back to that index. Take a slug out of
# this set to bring the page back.
HIDDEN = {"joopiter-son-of-a-pharaoh"}


def lead(slug):
    return "%s-%02d.jpg" % (slug, COVER.get(slug, 1))


def case(slug, title, meta, paras, work_label, work_items, extra=None):
    # A case study opens on a standfirst, not the About page's display lede --
    # these first paragraphs run 250-500 characters and would be a slab at 33px.
    blocks = [{"type": "intro", "text": paras[0]}]
    blocks += [{"type": "p", "text": p} for p in paras[1:]]
    if work_items:
        blocks.append({"type": "h2", "text": work_label})
        blocks.append({"type": "list", "items": work_items})
    for h, items in (extra or []):
        blocks.append({"type": "h2", "text": h})
        blocks.append({"type": "list", "items": items})
    blocks.append({"type": "h2", "text": "Gallery"})
    blocks.append(gallery(slug))
    page = {
        "slug": "work/" + slug,
        "title": title,
        "kicker": meta,
        "lead": lead(slug),
        "back": {"href": "work/", "label": "All projects"},
        "metaDescription": paras[0][:180],
        "blocks": blocks,
    }
    if slug in HIDDEN:
        page["hidden"] = True
    return page


CASES = [
    case(
        "joopiter-son-of-a-pharaoh",
        "Pharrell Williams: Son of a Pharaoh",
        "JOOPITER",
        ["JOOPITER is a digital-first auction house and content platform founded by Pharrell Williams. Launched in 2022, JOOPITER serves as a space for collectors, curators, and creators to discover and explore rare cultural artifacts. The platform focuses on honoring these items by highlighting their provenance and intrinsic relevance through carefully curated auctions.",
         "The inaugural auction, titled “Son of a Pharaoh,” featured 52 unique items from Pharrell’s personal collection, including custom jewelry, fashion pieces, and other rare collectibles.",
         "JOOPITER aims to create a community and commerce destination where budding and seasoned collectors can engage with cultural artifacts. The site is enriched by original editorial content and archival imagery that delve into the stories behind the items."],
        None, None),
    case(
        "youtube-fashion-beauty-launch",
        "YouTube Fashion & Beauty Launch",
        "YouTube · MAS",
        ["To introduce the newly minted YouTube Fashion & Beauty vertical to New York Fashion Week, YouTube held a star-studded launch party hosted by Derek Blasberg. The occasion called for an elegant-meets-edgy aesthetic with a plush lounge, art installations, social moments, and custom-fabricated stage anchoring a headline performance by Future. The guest list included A-listers Serena Williams, Gigi & Bella Hadid, Diplo, Alexander Wang, and many more. This event was designed and produced by MAS Event + Design."],
        "Project Contributions",
        ["Partnered with CAA to secure and produce a performance by Future",
         "Managed the creative development and fabrication of the custom stage and art installations",
         "Collaborated with Cha Cha Matcha to develop a co-branded pop-up bar",
         "Developed and produced brand visual identity",
         "Sourced and produced gifting moment",
         "Owned day-to-day client relations",
         "Oversaw event production, logistics, and security planning"]),
    case(
        "google-pixel-3-grammy-activation",
        "Google Pixel 3 × Childish Gambino Activation",
        "Google · MAS",
        ["Announcing the release of the Childish Gambino Playmoji for the Pixel 3, Google brought an immersive social activation to the Grammys Celebration at the Los Angeles Convention Center. Pulling inspiration from the lighting design in Childish Gambino’s live performances and the Pixel’s sleek aesthetic, the activation challenged influencers and industry guests to a dance battle with Childish Gambino in a life-size version of the device.",
         "The action was all captured on the Pixel 3 and guests walked away with shareable content of their dance-off with the winner of four Grammy awards that evening. Influencers such as Quincy, a #teampixel member with 4.5 million followers, and designer Jerome Lamaar shared their #pixeldanceoff to create a multi-touchpoint campaign leveraging Google’s national paid media. This event was designed and produced by MAS Event + Design."],
        "Project Contributions",
        ["Designed user experience flow leveraging the Pixel 3’s exclusive augmented reality technology",
         "Owned project management, planning, and logistics"],
        [("Awards",
          ["Adweek finalist for Best Use of Celebrity in an Experiential Activation",
           "Event Marketer’s Experience Design & Technology Award"])]),
    case(
        "trillectro",
        "Trillectro Music Festival",
        "Trillectro",
        ["Trillectro is recognized as the DMV’s first hip-hop and electronic music festival. The name Trillectro, a portmanteau of “trill” (meaning “authentic” in hip-hop circles) and “electro” (short for “electronic”), embodies the festival’s credo of bridging the gap between music genres.",
         "Respected as a platform for who and what is next, Trillectro worked closely with a plethora of the music industry’s emerging talents and certified stars to create an engaging, unforgettable experience. Integrated partnerships with Monster, Lyft, and Tidal elevated the attendee experience and secured financial support. Trillectro featured performances by Kid Cudi, SZA, 2 Chainz, Young Thug, RL Grime, Carnage, and many more at the legendary Merriweather Post Pavilion.",
         "With only 4 core team members, delivering 5 music festivals called for all of us to wear many hats."],
        "Responsibilities",
        ["Comprehensive Marketing Strategy",
         "Digital Marketing",
         "Partner Relations and Business Development",
         "On-site Activation Lead",
         "Talent Booking and Management"]),
    case(
        "youtube-music-rolling-stone-relaunch",
        "YouTube Music @ Rolling Stone Relaunch",
        "YouTube Music · MAS",
        ["For this project, I managed and produced YouTube Music’s partnership elements for Rolling Stone’s relaunch event featuring a live performance from Shawn Mendes.",
         "I led comms across two brand teams and multiple agency partners on co-branded concepts. I also led the collaboration between the MAS creative team and multiple vendors to develop and activate two interactive product demos for the DSP.",
         "The result was a seamless guest experience with key brand and product touchpoints for 500 VIP attendees including C-suite execs, elite media, and top influencers. This event was designed and produced by MAS Event + Design."],
        "Project Contributions",
        ["Maximized YouTube Music’s visibility during Rolling Stone partnership"]),
    case(
        "youtube-music-megan-thee-stallion",
        "YouTube Music × Megan Thee Stallion",
        "YouTube Music · MAS",
        ["YouTube Music and Megan Thee Stallion hosted a Celebration of the Fearless Women in Music, a night to honor the contributions of women in front of the lens and behind the scenes. The celebration took place at Spring Place in Beverly Hills, which was transformed into a beautiful lounge with tasteful pops of branding. The night was soundtracked by DJ Osh Kosh and culminated in a gracious moment from Megan Thee Stallion, taking over the dancefloor to engage with attendees. This event was designed and produced by MAS Event + Design."],
        "Project Contributions",
        ["Brand management and visual identity",
         "Overall event planning and logistics",
         "Spatial design",
         "Food and beverage design",
         "Partnering with ICM for talent booking"]),
    case(
        "youtube-grammy-party-nyc",
        "YouTube Grammy Party NYC",
        "YouTube · MAS",
        ["Celebrating the Grammys’ return to New York, YouTube threw a party hosted by Lyor Cohen. The night featured performances by Nas, Grandmaster Flash, D-Nice, and Vashtie. Other notable guests included Quincy Jones, Diplo, Camila Cabello, Jared Leto, Lala, Terrence J, and more. This event was designed and produced by MAS Event + Design."],
        "Project Contributions",
        ["Team Lead", "Brand Management", "Client Relations",
         "On-site Activation Lead", "Talent Management", "Creative Ideation"]),
    case(
        "youtube-latin-american-creator-summit",
        "YouTube Latin American Creator Summit",
        "YouTube · MAS",
        ["YouTube amplified community building among Latin American Creators with a 3-day summit in Los Angeles. The summit created spaces for candid and personal conversations between YouTube executives and Creators about the vision for the platform moving forward and the state of content creation as a whole. The main stage also hosted fun activities balancing out heavier discussions as well as special guest appearances from Pitbull and Hannah Beachler.",
         "Intentional themes and design channeled the vibrancy of Latin American culture allowing the Creators to feel seen. Each creator was greeted with a custom gift and collateral in their native language. This event was designed and produced by MAS Event + Design."],
        "Project Contributions",
        ["Guided YouTube’s efforts to recognize the Latin American creator community",
         "Created and executed culturally relevant event programming for the 3-day experience covering design, themes, music, food, and gifting",
         "Developed visual branding and collateral in English, Spanish, and Portuguese",
         "Coordinated translation services for Spanish, Portuguese, and English language speakers and guests to experience the event in their native language",
         "Managed overall project planning, budget, and logistics"]),
    case(
        "youtube-black-creator-summit",
        "#YouTubeBlack Creator Summit",
        "YouTube · MAS",
        ["YouTube hosted 100 Black Creators for the #YouTubeBlack Creator Summit in Washington, D.C., a city full of rich Black history from Howard University to the legendary Ben’s Chili Bowl. The event consisted of a week of curated, thoughtful programming. The Line Hotel provided a beautiful backdrop for YouTube to recognize and support established and emerging Black Creators.",
         "Programming included conversations with Naomi Campbell, Janelle Monáe, Steve Pamon (Parkwood COO), LaKeith Stanfield, YouTube Execs, and Creators. Following the panels, Creators connected over decadent group meals and guided activities. Each day’s momentum culminated in vibrant parties at the Black-owned cultural hub, Diet Starts Monday, and the cutting-edge music venue, Flash. This event was designed and produced by MAS Event + Design."],
        "Project Contributions",
        ["Served as the lead producer and client lead for the overall #YouTubeBlack Creator Summit experience",
         "Acted as the driving force behind creative development of event narratives and themes pulling from modern and nostalgic Black culture references",
         "Identified and booked noteworthy Black DJs, entertainers, photographers, and videographers to elevate the Creator experience",
         "Curated custom music playlists featuring contemporary, throwback, and global music by Black artists",
         "Scouted and secured venues that were both culturally relevant and on-brand",
         "Managed all event planning, logistics, venue, and vendor relations"]),
    case(
        "google-mixtape",
        "Google Mixtape",
        "Google · MAS",
        ["To provide a surprise and delight moment during Advertising Week, Google invited over 2,000 guests to pull away from their screens by shipping a personalized “Mixtape” experience to pair with the brand’s audio-first content developed specifically for the advertising industry’s top virtual event.",
         "The Mixtape box included one of six guided activity kits, which matched guests to their interests shared during registration, for them to dive into while listening to their personalized audio content. The packaging ushered guests on a journey using playful design, thoughtful materials, and intriguing reveal moments. The hero item was a retro-style cardboard Walkman with a built-in Bluetooth speaker which transformed the guests’ smartphone screens into cassette tapes.",
         "The unique Mixtape experience created the perfect analog world for digital content, elevating the brand’s message above ubiquitous screen-only approaches. This event was designed and produced by MAS Event + Design."],
        "Project Contributions",
        ["Oversaw end-to-end project management including creative development, execution, logistics, and COVID safety prep",
         "Ideated, sourced, and secured elements for activity kits featuring items from small and BIPOC businesses",
         "Successfully executed fulfillment of 2,231 Mixtape boxes over seven days",
         "Achieved on-time delivery within a single-day arrival window"]),
]

ABOUT = {
    "slug": "",
    "title": "About",
    "label": "About",
    "nav": True,
    "blocks": [
        {"type": "lede",
         "text": "The best campaigns get built twice. Once for the room, and again for everyone who sees it afterwards."},
        {"type": "p",
         "text": "I create marketing campaigns and experiences that amplify music and culture for tech brands, music platforms and festivals. I’ve spent over 20 years at the forefront of culture as a DJ, sneakerhead and dot connector, and more than a decade of that working with some of the best known brands in the world. Right now that means Apple Music, Apple TV and Beats. Before it meant JOOPITER, YouTube, Google, and a festival called Trillectro that four of us built from nothing. I bring a creative director’s vision, a music supervisor’s ear and a producer’s type-A structure to every project."},
        {"type": "image", "src": "about-portrait.jpg",
         "alt": "Stephen Greenwood on the beach with his dog"},
        {"type": "h2", "text": "Areas of Expertise"},
        {"type": "cells", "items": [
            "Music & Culture Marketing",
            "Brand Campaign Strategy",
            "Experiential Marketing",
            "Earned Media & Social",
            "Brand Partnerships",
            "Artist & Label Relationships"]},
    ],
}

STORY = {
    "slug": "story",
    "title": "Story",
    "label": "Story",
    "nav": True,
    "lead": lead("story"),
    "metaDescription": "From rural North Carolina to DC, New York and Los Angeles — DJing, Trillectro, Skin Valley, and the agency years.",
    "blocks": [
        {"type": "p", "text": "As a kid in rural North Carolina, my love for Hip-Hop and sneakers stood out like a sore thumb. In college I worked out that throwing parties was the fastest way to meet everyone on campus, so I bought DJ gear and went legit, and ended up putting on some of UNCW’s largest parties and concerts. After graduating I followed a job to DC and fell in love with the city’s cultural diversity. I kept DJing sweaty parties that started in my living room and spilled out onto the block. I joined the GEICO mobile app team, which fed a long-time passion for consumer tech, and used what I learned there to build More than Friends, an R&B party series I grew by funneling RSVPs into an email list that got bigger every month."},
        {"type": "p", "text": "The friends I threw parties with started Trillectro, a groundbreaking independent Hip-Hop and Electronic music festival, and I became a core member of their small team. We got known for lineups built around emerging talent, with early performances from Travis Scott and GoldLink, and over six years we grew it to Merriweather Post Pavilion and marquee artists like Kid Cudi, Chance the Rapper and SZA. My part was the audience. I pushed growth across social, email and media partners like Genius and Hypebeast, year over year, and the festival ended up covered by Billboard, Complex and The Fader."},
        {"type": "p", "text": "Halfway through the Trillectro run I moved to New York, extended the festival’s reach by partnering with culture brands like Everyday People, and co-created Skin Valley, a monthly party at Brooklyn’s Kinfolk. I built its audience with a Twilio SMS chatbot that pointed thousands of party-goers to the next event, and it became the venue’s most successful series. Professionally I moved into the agency world around the same time, making experiences with YouTube Music, Google and Samsung and producing the YouTube Creators Summits across several years. The work kept bringing me to the West Coast, and eventually I moved to Los Angeles."},
        {"type": "p", "text": "The next chapter was JOOPITER, the digital auction house Pharrell Williams founded, where I came on as senior brand marketing manager. The company was brand new and so was the idea, so the job meant a little of everything. I ran the campaign around each auction, built the press and partner relationships, and helped shape the previews we held in New York, Paris and Hong Kong so every collection had somewhere beautiful to be seen and photographed. The first one, Son of a Pharaoh, was fifty-two pieces from Pharrell’s own collection and honestly no map for any of it. We had to make people care before we could sell a single thing. Terrifying, and the most fun I’ve had at work."},
        {"type": "p", "text": "These days I’m at Apple, leading brand experience across Apple Music, Apple TV and Beats. When there’s an album or a show worth getting excited about, I build the thing that gets people talking. A pop-up in Brooklyn for thirty years of Reasonable Doubt. A gallery in Miami with Highsnobiety during Art Basel. A whole Formula 1 season that ran for eight months rather than a single night, with Today at Apple sessions, a billboard in Times Square, the car at Apple Park, a weekend at the Miami GP with Beats, and a pizzeria in Little Italy that we turned into Monza for the Italian Grand Prix. A few hundred people walk through the door and that’s lovely, but what I’m really building for is the millions who see it later on their phones."},
        {"type": "p", "text": "The budgets have gotten bigger and there are more people who have to say yes, but the room itself is still the smallest part of it. I learned that at Trillectro, where four of us grew a festival with Genius, Hypebeast and an email list, and it’s still how I think about the work. Build something people want to photograph, then make sure it’s everywhere the next morning."},
        {"type": "h2", "text": "Along the way"},
        gallery("story", cols=2),
    ],
}

RESUME = {
    "slug": "resume",
    "title": "Resume",
    "label": "Resume",
    "nav": True,
    "metaDescription": "Agencies, brand partners, and label and platform contacts — Stephen Greenwood.",
    "blocks": [
        # Split brand-side from agency-side. Trillectro and GEICO sit with the
        # brands: a festival he helped run and an in-house app team, neither an
        # agency. Both keep the links they came over from Squarespace with.
        {"type": "h2", "text": "Brand Experience"},
        {"type": "cells", "items": [
            "Apple Music",
            "Apple TV",
            "Beats",
            "JOOPITER",
            {"label": "Trillectro", "url": "https://www.instagram.com/trillectro/"},
            {"label": "GEICO", "url": "https://www.geico.com/"}]},
        {"type": "h2", "text": "Agency Experience"},
        {"type": "cells", "items": [
            {"label": "MAS", "url": "https://moremas.com/"},
            {"label": "McKinney", "url": "https://mckinney.com/"},
            {"label": "360i", "url": "https://www.360i.com/"}]},
        {"type": "h2", "text": "Clients & Brand Partners"},
        {"type": "cells", "items": [
            "Google", "Google Consumer Products", "Google Pixel",
            "Google Cloud Services", "Facebook", "Samsung Mobile", "YouTube",
            "YouTube Music", "YouTube Creator Marketing",
            "YouTube Fashion & Beauty", "YouTube News", "YouTube TV", "AOL",
            "Absolut", "PepsiCo & Mountain Dew", "Monster Energy",
            "Jack Daniel’s", "Hypebeast"]},
        {"type": "h2", "text": "Contacts at Labels and Music Platforms"},
        {"type": "cells", "items": [
            "Capitol Records", "Virgin Music", "RCA Records", "Warner Records",
            "Columbia Records", "Atlantic Records", "Roc Nation", "Interscope",
            "EQT Recordings", "LVRN", "YouTube Music", "Spotify", "SoundCloud", "Audius"]},
    ],
}

WORK = {
    "slug": "work",
    "title": "Projects",
    "label": "Projects",
    "nav": True,
    "metaDescription": "Case studies from the YouTube, Google and Trillectro years.",
    "blocks": [
        {"type": "p",
         "text": "Longer-form case studies from the YouTube, Google and Trillectro years — the work that came before the Apple and JOOPITER chapters."},
        {"type": "cards", "items": [
            {"title": c["title"],
             "href": c["slug"] + "/",
             "image": c["lead"]}
            for c in CASES if not c.get("hidden")]},
    ],
}

# Old Squarespace URLs, so anything already linked or indexed still lands.
REDIRECTS = {
    "/home": "/archive/work/",
    "/story": "/archive/story/",
    "/resume": "/archive/resume/",
    # joopiter-son-of-a-pharaoh is shelved (see HIDDEN), so its old URL goes
    # to the index rather than a page that is not built.
    "/home/pharrell-williams-son-of-a-pharoah": "/archive/work/",
    "/home/ytfashion1": "/archive/work/youtube-fashion-beauty-launch/",
    "/home/google-pixel-3-grammy-activation": "/archive/work/google-pixel-3-grammy-activation/",
    "/home/trillectro": "/archive/work/trillectro/",
    "/home/youtube-music-rolling-stone-relaunch": "/archive/work/youtube-music-rolling-stone-relaunch/",
    "/home/youtube-x-meg-thee-stallion-fearless-women-in-music": "/archive/work/youtube-music-megan-thee-stallion/",
    "/home/youtube-grammy-party-nyc": "/archive/work/youtube-grammy-party-nyc/",
    "/home/ytlatam1": "/archive/work/youtube-latin-american-creator-summit/",
    "/home/ytbcs": "/archive/work/youtube-black-creator-summit/",
    "/home/google-mixtape": "/archive/work/google-mixtape/",
    "/cart": "/",
}

doc = {
    "baseUrl": "https://withgreenwood.com/archive",
    "homeUrl": "/",
    "homeLabel": "Work",
    "kicker": "Archive",
    "redirects": REDIRECTS,
    "metaDescription": "Stephen Greenwood — brand marketing and experience across music, sport and culture. Background, areas of expertise, project case studies, and the long story.",
    "pages": [ABOUT, STORY, RESUME, WORK] + CASES,
}

OUT.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
print("wrote %s (%d pages)" % (OUT, len(doc["pages"])))
