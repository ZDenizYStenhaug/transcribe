import os

import transcriber as tr

def main():
    text = "What have you done? I hate you!"
    print(sa.get_sentiment_score(text))
    while True:
        # file = input("Please enter the file name: \n")

        bucket_uri = os.getenv("S3_BUCKET_URI")
        bucket_name = os.getenv("S3_BUCKETNAME")

        choice = input("\nPlease chose:\n1: list files on s3 bucket\n" +
                       "2: list existing jobs\n" +
                       "3: exit\n")

        if choice == "1":
            s3(bucket_name, bucket_uri)
        elif choice == "2":
            job()

        elif choice == "3":
            print("\nExiting. Thank you^^")
            break
        else:
            print("Invalid input. Please try again.")


def job():
    tr.list_transcribe_jobs()
    while True:

        choice = input("\nPlease chose:\n1: delete job\n" +
                       "2: go back\n")
        if choice == "1":
            delete_choice = input("Please type the number of the job you'd like to delete.")
            tr.delete_job(delete_choice)
        elif choice == "2":
            break
        else:
            print("Invalid input. Please try again.")


def s3(bucket_name, bucket_uri):
    while True:
        files = tr.list_s3_files(bucket_name)
        choice = input("\nPlease chose:\n1: delete file\n" +
                       "2: upload file\n" +
                       "3: transcribe file \n" +
                       "4: transcribe and sentiment analysis\n" +
                       "5: go back\n")
        if choice == "1":
            delete_filename = input("Please type the name of the file you'd like to delete.")
            tr.delete_file_from_s3(delete_filename, bucket_name)

        elif choice == "2":
            upload_filename = input("Please type the filename you'd like to upload.\n(The file needs to be an mp3")
            tr.upload_file_to_s3(upload_filename, bucket_name)

        elif choice == "3":
            transcribe_filename = input("Please type the name of the file you'd like to transcribe.")
            if tr.check_file_exists_s3(transcribe_filename, bucket_name):
                while True:
                    count = input("\nPlease enter the number of times you'd like to transcribe this file:\n ")
                    if count.isnumeric():
                        tr.transcribe_loop(transcribe_filename, bucket_uri, count)
                        break
                    else:
                        print("Invalid input. Please type a number")

        elif choice == "4":
            transcribe_filename = input("Please type the name of the file you'd like to transcribe and perform "
                                        "sentiment analysis.")

        elif choice == "5":
            break
        else:
            print("Invalid input. Please try again.")


if __name__ == '__main__':
    main()
