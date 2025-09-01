import os
from dotenv import load_dotenv
load_dotenv()

from litellm import acompletion
import json

provider_keys = {
    "gemini": os.environ.get("GEMINI_API_KEY"),
    "groq": os.environ.get("GROQ_API_KEY"),
    "openai": os.environ.get("OPENAI_API_KEY"),
    "anthropic": os.environ.get("ANTHROPIC_API_KEY")
}

provider_models = {
    "gemini": "gemini-2.0-flash",
    "groq": "openai/gpt-oss-120b",
    "openai": "gpt-5-mini-2025-08-07",
    "anthropic": "claude-sonnet-4-20250514"
}

def get_llm_model_and_api_key():
    api_key = ""
    model_name = ""
    for provider in provider_keys:
        if provider_keys[provider]:
            model_name = f"{provider}/{provider_models[provider]}"
            api_key = provider_keys[provider]
            return model_name, api_key

    if api_key == "":
        raise ValueError("No API key found")


def get_system_prompt(device_details):
    system_prompt = f"""
        You are an expert SQL assistant. Your task is to convert natural language questions into SQL queries and return it in a JSON object with a single key 'query'.
        You must only generate a single, valid SQL query inside the JSON. Do not add any explanations or introductory text.
        The database dialect is Timescaledb.

        database_name: energy_monitor
        schema: public

        These are the important tables of the database

        table_name: device
        description: contains device information like name, user_id , product_id
        columns:
            id 	        ( UUID )
            name 	    ( VARCHAR(50) )
            user_id 	( INTEGER ) (Foreign Key)
            product_id 	( INTEGER ) (Foreign Key)
            created_at 	( TIMESTAMP )


        table_name: product
        description: contains product information like name, type, etc.
        columns:
            id 	        ( INTEGER )
            name 	    ( VARCHAR(50) )
            type 	    ( VARCHAR(50) )
            description ( VARCHAR )

        table_name: telemetry
        description: contains timestamped telemetry data published by devices. It captures the power consumption at a given timestamp.
        columns:
            timestamp 	    ( TIMESTAMP )
            device_id 	    ( UUID ) (Foreign Key)
            energy_watts 	( DOUBLE PRECISION )


        ### Examples

        -- Question: What was the energy usage of my devices in last one week?
        {{
            "query": "SELECT device_id, (AVG(telemetry.energy_watts) * (EXTRACT(epoch FROM (MAX(telemetry.timestamp) - MIN(telemetry.timestamp))) / 3600)) / 1000 AS total_kwh FROM telemetry WHERE device_id in ('e35a4495-5313-4a15-b854-5c196b0e94a9','2486c5ab-d4ce-45b0-aebb-9e99ced3b012','a0f4e75d-26aa-4a7a-a982-d630b287e0c3') AND timestamp > now() - INTERVAL '7 days' GROUP BY device_id"
        }}


        Below are the device details belonging to the user.
        {json.dumps(device_details, indent=2)}

        You are allowed to only perform select query on the telemetry table, utilizing only the above device_ids. Always limit your query to atmost 500 results.

        """
    return system_prompt


async def get_sql_query(user_question, system_prompt, model_name, api_key):
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_question},
    ]
    resp = await acompletion(
        model=model_name,
        api_key=api_key,
        messages=messages,
        response_format={"type": "json_object"})
    
    sql_query = json.loads(resp.choices[0].message.content)['query']
    return sql_query


async def generate_final_response(user_question, sql_query, sql_query_result, device_details, model_name, api_key):
    
    prompt = (
        "Given the following user question, device details, corresponding SQL query, "
        "and SQL result, answer the user question.\n\n"
        f"Question: {user_question}\n"
        f"Device Details: {device_details}\n"
        f"SQL Query: {sql_query}\n"
        f"SQL Result: {sql_query_result}"
    )
    messages = [
        {"role": "user", "content": prompt},
    ]
    resp = await acompletion(
        model=model_name,
        api_key=api_key,
        messages=messages,
    )    
    response = resp.choices[0].message.content
    return response