from datetime import datetime


def process_command(command, profile):

    if "hello" in command:

        return (
            f"Hello {profile['name']}. "
            f"I am {profile['assistant_name']}."
        )

    elif "my name" in command:

        return f"Your name is {profile['name']}."

    elif "my college" in command:

        return f"Your college is {profile['college']}."

    elif "my city" in command:

        return f"You live in {profile['city']}."

    elif "time" in command:

        time = datetime.now().strftime("%I:%M %p")

        return f"The current time is {time}."

    elif "date" in command:

        date = datetime.now().strftime("%d %B %Y")

        return f"Today is {date}."

    elif "stop" in command:

        return "EXIT"

    else:

        return (
            "I don't know this command yet."
        )