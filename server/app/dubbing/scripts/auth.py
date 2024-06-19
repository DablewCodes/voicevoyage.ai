#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Google Authentication Modules
from googleapiclient.discovery import build
from google.oauth2 import service_account
import os
import traceback

# Google Cloud Globals
# GOOGLE_TTS_API = None
# GOOGLE_TRANSLATE_API = None


#################################################################################################
################################## GOOGLE AUTHORIZATION #########################################
#################################################################################################
# The CLIENT_SECRETS_FILE variable specifies the name of a file that contains
# the OAuth 2.0 information for this application, including its client_id and
# client_secret. You can acquire an OAuth 2.0 client ID and client secret from
# the {{ Google Cloud Console }} at https://cloud.google.com/console
# Please ensure that you have enabled the Text to Speech API for your project.
# For more information about the client_secrets.json file format, see:
# https://developers.google.com/api-client-library/python/guide/aaa_client_secrets


# Authorize the request and store authorization credentials.
def get_authenticated_service():
    global GOOGLE_TTS_API
    global GOOGLE_TRANSLATE_API

    # TTS API Info
    GOOGLE_TTS_API_SERVICE_NAME = "texttospeech"
    GOOGLE_TTS_API_VERSION = "v1"
    TTS_DISCOVERY_SERVICE_URL = (
        "https://texttospeech.googleapis.com/$discovery/rest?version=v1"
    )

    # Translate API Info
    # https://translate.googleapis.com/$discovery/rest?version=v3 # v3 or beta v3beta1
    GOOGLE_TRANSLATE_API_SERVICE_NAME = "translate"
    GOOGLE_TRANSLATE_API_VERSION = "v3beta1"
    TRANSLATE_DISCOVERY_SERVICE_URL = (
        "https://translate.googleapis.com/$discovery/rest?version=v3beta1"
    )
    GOOGLE_API_SCOPES = [
        "https://www.googleapis.com/auth/cloud-platform",
        "https://www.googleapis.com/auth/cloud-translation",
    ]
    credentials = service_account.Credentials.from_service_account_file(
        os.path.join(
            os.getcwd(),
            "app/credentials",
            str(os.environ.get("GOOGLE_CREDENTIALS_FILE")),
        ),
        scopes=GOOGLE_API_SCOPES,
    )

    # Build tts and translate API objects
    GOOGLE_TTS_API = build(
        GOOGLE_TTS_API_SERVICE_NAME,
        GOOGLE_TTS_API_VERSION,
        credentials=credentials,
        discoveryServiceUrl=TTS_DISCOVERY_SERVICE_URL,
    )
    GOOGLE_TRANSLATE_API = build(
        GOOGLE_TRANSLATE_API_SERVICE_NAME,
        GOOGLE_TRANSLATE_API_VERSION,
        credentials=credentials,
        discoveryServiceUrl=TRANSLATE_DISCOVERY_SERVICE_URL,
    )

    return GOOGLE_TTS_API, GOOGLE_TRANSLATE_API


def gcp_authentication():
    global GOOGLE_TTS_API, GOOGLE_TRANSLATE_API
    try:
        (
            GOOGLE_TTS_API,
            GOOGLE_TRANSLATE_API,
        ) = get_authenticated_service()  # Create authentication object
    except Exception as e:
        traceback.print_exc()  # Prints traceback
        print(f"\nError: Something went wrong during authentication: {e}")
        return -1
    return GOOGLE_TTS_API, GOOGLE_TRANSLATE_API


#################################################################################################
################################## GOOGLE AUTHORIZATION #########################################
#################################################################################################

# GOOGLE_TTS_API, GOOGLE_TRANSLATE_API = gcp_authentication()
