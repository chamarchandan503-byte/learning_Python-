import json

from voice.listen import listen
from voice.speak import speak
from brain.commands import process_command


# Load personal data
with open(
    "personal/profile.json",
    "r",
    encoding="utf-8"
) as file:

    profile = json.load(file)


def main():

    speak(
        f"Hello {profile['name']}. "
        f"{profile['assistant_name']} is ready."
    )

    while True:

        command = listen()

        if command:

            response = process_command(
                command,
                profile
            )

            if response == "EXIT":

                speak(
                    f"Goodbye {profile['name']}."
                )

                break

            speak(response)


if __name__ == "__main__":
    main()