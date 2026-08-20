import os
import requests

# --- CONFIGURATION ---
RIOT_API_KEY = os.environ.get("RIOT_API_KEY")
NTFY_TOPIC = "riot_tracker_alert_7712"  # Match your subscribed ntfy topic

PLAYERS_TO_MONITOR = [
    {"game_name": "Faker", "tag_line": "KR1", "region": "asia", "platform": "kr"},
    {"game_name": "Doublelift", "tag_line": "NA1", "region": "americas", "platform": "na1"},
]

HEADERS = {"X-Riot-Token": RIOT_API_KEY}


def get_puuid(game_name: str, tag_line: str, region: str) -> str:
    url = f"https://{region}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
    res = requests.get(url, headers=HEADERS)
    res.raise_for_status()
    return res.json()["puuid"]


def check_active_game(puuid: str, platform: str):
    url = f"https://{platform}.api.riotgames.com/lol/spectator/v5/active-games/by-summoner/{puuid}"
    res = requests.get(url, headers=HEADERS)
    if res.status_code == 200:
        return res.json()
    return None


def send_push_notification(title: str, message: str):
    requests.post(
        f"https://ntfy.sh/{NTFY_TOPIC}",
        data=message.encode("utf-8"),
        headers={"Title": title, "Priority": "high", "Tags": "swords,video_game"},
    )


def main():
    if not RIOT_API_KEY:
        print("Missing RIOT_API_KEY environment variable.")
        return

    for player in PLAYERS_TO_MONITOR:
        identifier = f"{player['game_name']}#{player['tag_line']}"
        try:
            puuid = get_puuid(player["game_name"], player["tag_line"], player["region"])
            game_data = check_active_game(puuid, player["platform"])

            if game_data:
                queue_id = game_data.get("gameQueueConfigId")
                game_id = game_data.get("gameId")
                game_length_secs = game_data.get("gameLength", 0)

                # Queue 420 = Ranked Solo/Duo.
                # Only alert if the game recently started (< 8 minutes) to avoid repetitive spam.
                if queue_id == 420 and game_length_secs < 480:
                    mins = game_length_secs // 60
                    msg = f"{identifier} is in a Ranked Solo match! (Elapsed: ~{mins}m, Match ID: {game_id})"
                    print(f"[ALERT] {msg}")
                    send_push_notification("Ranked Solo Match Found", msg)
                else:
                    print(f"{identifier} is in-game (Queue: {queue_id}), no new alert needed.")
            else:
                print(f"{identifier} is not currently in a match.")

        except Exception as e:
            print(f"Error checking {identifier}: {e}")


if __name__ == "__main__":
    main()
