import speech_recognition as sr


def listen():

    recognizer = sr.Recognizer()

    with sr.Microphone() as source:

        print("Listening...")

        recognizer.adjust_for_ambient_noise(
            source,
            duration=0.5
        )

        try:

            audio = recognizer.listen(
                source,
                timeout=5,
                phrase_time_limit=8
            )

            command = recognizer.recognize_google(
                audio,
                language="en-IN"
            )

            print("You:", command)

            return command.lower()

        except sr.WaitTimeoutError:
            return ""

        except sr.UnknownValueError:
            return ""

        except sr.RequestError:
            return ""