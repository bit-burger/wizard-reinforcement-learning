import random

from features.wizard.konstanten import *


def get_color_name(color: Color) -> str:
    color_names = {
        Color.RED: "Rot",
        Color.GREEN: "Gruen",
        Color.BLUE: "Blau",
        Color.YELLOW: "Gelb"
    }
    return color_names.get(color, "UNKNOWN_COLOR")


def print_card(card: Card):
    if card.value == 14:
        print("Wizzard")
    elif card.value == 0:
        print("Narre")
    elif card.value != -1:
        print(f"{get_color_name(card.color)} {card.value}")


def print_stich(stich: List[Card]):
    print("Aktuell liegende Karten:\n")
    print("Trumpf:    ", end="")
    print_card(trump)
    print()
    for card in stich:
        print("\t   ", end="")
        print_card(card)


def print_hand(player: int):
    print(f"\n{players[player].name} Karten:\n")
    for i, card in enumerate(players[player].hand):
        if i >= current_round:
            break
        if 0 <= card.value < 15:
            print(f"\t{i + 1}: ", end="")
            print_card(card)
    print()


def outputToBot(player: int) -> Outputdata:
    output = Outputdata()
    output.hand = players[player].hand.copy()
    # TODO: Complete OutputData
    return output


def is_valid_input() -> int:
    while True:
        try:
            return int(input())
        except ValueError:
            print("Falsche eingabe")


def get_input(modus: int, name: str) -> int:
    if modus == 1:  # stiche callen
        while True:
            print(f"{name} wie viele Stiche denkst du, wirst du machen?")
            input_value = is_valid_input()
            if 0 <= input_value <= current_round:
                return input_value
            print(f"Falsche Eingabe. Bitte gib eine Zahl zwischen 0 und {current_round} ein.")
    elif modus == 2:  # Karte legen
        while True:
            print(f"\n{name}, welche Karte willst du ausspielen?")
            card_index = is_valid_input() - 1
            if 0 <= card_index <= current_round:
                return card_index
            print("\nWird nicht akzeptiert. Versuche es erneut.")
    return 0


def initialize_players():
    for i in range(PLAYERS):
        players[i].name = f"Player {i + 1}"
        players[i].score = 0


def initialize_deck():
    global deck
    deck = [Card(i % 15, Color(i % 4)) for i in range(DECK_SIZE)]


def shuffle_deck():
    random.shuffle(deck)


def deal_cards(round_hand_size: int):
    for i in range(round_hand_size):
        for k in range(PLAYERS):
            players[k].hand[i] = deck[PLAYERS * i + k]
    for j in range(round_hand_size, 15):
        for k in range(PLAYERS):
            players[k].hand[j] = Card(-1, Color.NILL)


def clean_hand(player: int, card_index: int):
    players[player].hand[card_index:] = players[player].hand[card_index + 1:] + [Card(-1, Color.NILL)]


def determine_single_round_winner(played_Cards: List[Card]) -> int:
    temp_trick = played_Cards[0]
    winning_player = 0
    for i, current_card in enumerate(played_Cards):
        if (
                current_card.color == temp_trick.color or current_card.color == trump.color) and current_card.value > temp_trick.value:
            temp_trick = current_card
            winning_player = i
    return winning_player


def play_stich(start_spieler: int) -> int:
    played_Cards = [Card(-1, Color.NILL) for _ in range(PLAYERS)]
    global trick
    trick = Card(-1, Color.NILL)

    for x in range(PLAYERS):
        offset = (x + start_spieler) % PLAYERS
        while True:
            print_stich(played_Cards)
            print_hand(offset)
            card_index = get_input(2, players[offset].name)
            played_card = players[offset].hand[card_index]

            if trick.value == -1 and played_card.value not in [14, 0]:
                trick = Card(played_card.value, played_card.color)

            if played_card.color != trick.color and played_card.color != trump.color and played_card.value not in [14,
                                                                                                                   0]:
                if any(card.color in [trick.color, trump.color] and 1 < card.value < 14 for card in
                       players[offset].hand[:current_round]):
                    print("\nDu musst die Farbe bedienen, wenn du kannst. Versuche es erneut.")
                    continue

            clean_hand(offset, card_index)
            print(f"{players[offset].name} spielt ", end="")
            print_card(played_card)
            print("\n________________________________________________")
            played_Cards[x] = played_card
            break

    return (determine_single_round_winner(played_Cards) + start_spieler) % PLAYERS


def play_round(round: int, start_spieler_runde: int):
    print(
        "Neue Runde\n________________________________________________\n________________________________________________")
    deal_cards(round)
    called_stiche = 0
    global trump
    trump = deck[round * PLAYERS + 1]

    for i in range(PLAYERS):
        while True:
            offset = (i + start_spieler_runde) % PLAYERS
            print("Trumpf:    ", end="")
            print_card(trump)
            print_hand(offset)
            players[offset].called_stiche = get_input(1, players[offset].name)
            if i == PLAYERS - 1 and called_stiche + players[offset].called_stiche == round:
                print(
                    "Die Summe der Vorhersagen ist gleich der Anzahl der Stiche, die in dieser Runde gemacht werden. Bitte korrigiere deine Vorhersage.")
                continue
            called_stiche += players[offset].called_stiche
            print("________________________________________________")
            break

    start_spieler_stich = start_spieler_runde
    for _ in range(round):
        start_spieler_stich = play_stich(start_spieler_stich)
        players[start_spieler_stich].gewonnene_stiche += 1
        print(
            f"{players[start_spieler_stich].name} hat den Stich gewonnen!\n________________________________________________")

    for player in players[:PLAYERS]:
        if player.gewonnene_stiche == player.called_stiche:
            player.score += 20 + 10 * player.called_stiche
        else:
            player.score -= 10 * abs(player.gewonnene_stiche - player.called_stiche)


def sort_players_by_score():
    players[:PLAYERS] = sorted(players[:PLAYERS], key=lambda x: x.score, reverse=True)


def print_scoreboard():
    sort_players_by_score()
    print("Das Spiel ist vorbei! Das Endergebnis ist:")
    for player in players[:PLAYERS]:
        print(f"{player.name}: {player.score}")


def settings():
    global PLAYERS, ROUNDS, MAX_HAND_SIZE
    PLAYERS = int(input("Wie viele Spieler spielen?\n"))
    while True:
        ROUNDS = int(input("Wie viele Runden sollen gespielt werden?\n"))
        if ROUNDS * PLAYERS <= DECK_SIZE:
            break
        print("Zu viele Runden für die Anzahl der Spieler")
    MAX_HAND_SIZE = int(input("Wie viele Karten sollen pro Runde ausgeteilt werden?\n"))


def main():
    settings()
    initialize_deck()
    shuffle_deck()
    initialize_players()

    start_spieler_runde = 0
    for round in range(1, ROUNDS + 1):
        global current_round
        current_round = round
        shuffle_deck()
        deal_cards(round)
        play_round(round, start_spieler_runde)
        start_spieler_runde = (start_spieler_runde + 1) % PLAYERS

    print_scoreboard()


if __name__ == "__main__":
    main()