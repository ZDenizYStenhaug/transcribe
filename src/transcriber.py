import os
import time
import boto3
import pandas as pd
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from datetime import datetime

import sentiment_analysis as sa

load_dotenv(verbose=True)

session = boto3.Session(
    aws_access_key_id=os.getenv('ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('SECRET_ACCESS_KEY'),
    region_name="eu-central-1")

session_s3 = session.resource('s3')

s3 = boto3.client('s3',
                  aws_access_key_id=os.getenv('ACCESS_KEY_ID'),
                  aws_secret_access_key=os.getenv('SECRET_ACCESS_KEY'),
                  region_name="eu-central-1")

transcribe_client = boto3.client('transcribe',
                                 aws_access_key_id=os.getenv('ACCESS_KEY_ID'),
                                 aws_secret_access_key=os.getenv('SECRET_ACCESS_KEY'),
                                 region_name="eu-central-1", )


def check_file_exists_s3(file, bucketName):
    """Checks if the file exists in the s3 bucket"""
    try:
        s3.head_object(Bucket=bucketName, Key=file)
    except ClientError:
        print("File doesn't exist in s3.")
        return False
    return True


def check_job_name(transcriptionName):
    existing_jobs = transcribe_client.list_transcription_jobs()
    for job in existing_jobs['TranscriptionJobSummaries']:
        if transcriptionName == job['TranscriptionJobName']:
            print("Overriding existing job..")
            transcribe_client.delete_transcription_job(TranscriptionJobName=transcriptionName)
            break


def delete_file_from_s3(file, bucket_name):
    """deletes the file in the s3 bucket"""
    if check_file_exists_s3(file, bucket_name):
        s3.delete_object(Bucket=bucket_name, Key=file)
        print("Removing file...")
        return True
    else:
        print("File not found.")
        return False


def delete_job(job_name):
    """ Deletes a transcription job. """
    try:
        transcribe_client.delete_transcription_job(
            TranscriptionJobName=job_name)
        print("Successfully deleted " + job_name + ".")
    except ClientError:
        print("Couldn't delete job %s.", job_name)


def get_s3_files(bucket_name):
    bucket = session_s3.Bucket(bucket_name)
    return bucket.objects.all()


def list_transcribe_jobs():
    """gets existing jobs in the transcribe service"""
    print("## Jobs in Transcribe ##")
    existing_jobs = transcribe_client.list_transcription_jobs()
    isEmpty = True
    for job in existing_jobs['TranscriptionJobSummaries']:
        print("* " + job['TranscriptionJobName'])
        isEmpty = False
    if isEmpty:
        print("No existing job")


def list_s3_files(bucket_name):
    print("\n ## Files in s3 ##")
    files = []
    bucket_objects = session_s3.Bucket(bucket_name).objects.all()
    isEmpty = True
    for bucket_object in bucket_objects:
        print("* " + bucket_object.key)
        files.append(bucket_object.key)
        isEmpty = False
    if isEmpty:
        print("No existing file")
    return files


def transcribe(filename, job_name, bucket_uri):
    # delete the existing job if there already is an existing job with the same name
    check_job_name(job_name)
    s3_uri = bucket_uri + filename
    file_format = "mp3"

    transcribe_client.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={'MediaFileUri': s3_uri},
        MediaFormat=file_format,
        LanguageCode='en-US'),
    count = 20
    sleep = 0.5
    t1_start = time.time()
    while count > 0:
        time.sleep(sleep)
        result = transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
        job_status = result['TranscriptionJob']['TranscriptionJobStatus']
        if job_status in ['COMPLETED', 'FAILED']:
            break
        sleep = sleep + (0.5 * (21 - count)) / 2
        print(f"transcribing... Current status is {job_status}.")
        count -= 1

    if result['TranscriptionJob']['TranscriptionJobStatus'] == "COMPLETED":
        t1_stop = time.time()
        time_taken_for_process = t1_stop - t1_start
        return result, time_taken_for_process, t1_start
    else:
        print("Transcription failed ><")


def transcribe_loop(filename, bucket_uri, count):
    job_name = (filename.split('.')[0]).replace(" ", "")
    # set the output filename
    now = datetime.now()
    dt_string = now.strftime("%d-%m-%y-%H-%M")
    output_filename = job_name + "_" + dt_string + "_" + count

    df = pd.DataFrame()
    for i in range(int(count)):
        result, time_taken_for_process, start_time = transcribe(filename, job_name, bucket_uri)

        data = pd.read_json(result['TranscriptionJob']['Transcript']['TranscriptFileUri'])
        text = data['results'][1][0]['transcript']
        avg_confidence = calculate_average_confidence(data)
        time_taken_for_job = (result['TranscriptionJob']['CompletionTime'] - result['TranscriptionJob']['StartTime'])\
            .total_seconds()
        sentiment = sa.get_sentiment_score(text)
        row = {"job_name": job_name,
               "start_time": start_time,
               "text": text,
               "avg_confidence": avg_confidence,
               "time_taken_for_job": time_taken_for_job,
               "time_taken_for_process": time_taken_for_process,
               "sentiment_score": sentiment}
        df = df.append(row, ignore_index=True)

    write_to_file(df, output_filename)


def upload_file_to_s3(file, bucket_name):
    """upload file to s3 bucket"""
    if not check_file_exists_s3(file, bucket_name):
        s3.upload_file(file, bucket_name, file)

        count = 5  # Attempt to confirm upload x amount of times
        sleep = 5
        while count > 0:
            time.sleep(5)
            if not check_file_exists_s3(file, bucket_name):
                print("uploading...")
                sleep = sleep + (5 * (6 - count))  # Add 5 x lapsed rounds in seconds for each attempt
            else:
                count = 0
            count -= 1
        print("Upload successful!")
    else:
        print("File already exists.")


def calculate_average_confidence(data):
    data_by_word = data['results'][0]
    confidence_sum = 0
    for data in data_by_word:
        confidence_sum += float(data['alternatives'][0]['confidence'])
    avg = confidence_sum / len(data_by_word)
    return avg


def write_to_file(df, filename):

    df.to_csv("../results/" + filename + ".csv", index=None, header=True)
