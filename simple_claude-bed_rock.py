"""
AWS Bedrock Claude Haiku 4.5 Integration
Connect to AWS Bedrock and send a prompt to Claude Haiku model
"""

import json
import os
from dotenv import load_dotenv
import boto3

# Step 1: Load environment variables from .env file
def load_environment():
    """Load AWS credentials from .env file"""
    load_dotenv()
    
    aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    aws_session_token = os.getenv('AWS_SESSION_TOKEN')
    aws_region = os.getenv('AWS_REGION')
    
    print("✓ Environment variables loaded from .env")
    print(f"  - Region: {aws_region}")
    
    return aws_access_key, aws_secret_key, aws_session_token, aws_region


# Step 2: Create AWS Bedrock client
def create_bedrock_client(access_key, secret_key, session_token, region):
    """Initialize AWS Bedrock runtime client"""
    try:
        client = boto3.client(
            'bedrock-runtime',
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            aws_session_token=session_token if session_token else None
        )
        print("✓ AWS Bedrock client created successfully")
        return client
    except Exception as e:
        print(f"✗ Error creating Bedrock client: {e}")
        raise


# Step 3: Send prompt to Claude Haiku 4.5 using Converse API
def send_prompt_to_claude(client, prompt):
    """Send a prompt to Claude Haiku 4.5 model using the Converse API"""
    
    # Model ID for Claude Haiku 4.5 (Cross-region)
    model_id = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
    
    # Prepare messages for Converse API
    messages = [
        {
            "role": "user",
            "content": [{"text": prompt}]
        }
    ]
    
    try:
        print(f"\n📤 Sending prompt to Claude Haiku 4.5...")
        print(f"   Model: {model_id}")
        print(f"   Prompt: '{prompt}'")
        
        # Call the Bedrock API using converse method
        response = client.converse(
            modelId=model_id,
            messages=messages,
            inferenceConfig={"maxTokens": 1024}
        )
        
        print("✓ Response received from AWS Bedrock")
        return response
        
    except Exception as e:
        print(f"✗ Error sending prompt to Bedrock: {e}")
        raise


# Step 4: Parse and display the response
def parse_response(response):
    """Parse the response from Claude Haiku using Converse API"""
    try:
        # Extract the text content from converse response
        if 'output' in response and 'message' in response['output']:
            message = response['output']['message']
            if 'content' in message and len(message['content']) > 0:
                content = message['content'][0]['text']
                return content
        return "No content in response"
            
    except Exception as e:
        print(f"✗ Error parsing response: {e}")
        raise


# Step 5: Main execution
def main():
    """Main function to orchestrate the workflow"""
    try:
        print("=" * 60)
        print("AWS Bedrock Claude Haiku 4.5 Integration")
        print("=" * 60)
        
        # Step 1: Load environment variables
        access_key, secret_key, session_token, region = load_environment()
        
        # Step 2: Create Bedrock client
        client = create_bedrock_client(access_key, secret_key, session_token, region)
        
        # Step 3: Define the prompt
        prompt = "Who is the prime minister of India as of today?"
        
        # Step 4: Send prompt to Claude Haiku
        response = send_prompt_to_claude(client, prompt)
        
        # Step 5: Parse and display response
        answer = parse_response(response)
        
        print("\n" + "=" * 60)
        print("📥 RESPONSE FROM CLAUDE HAIKU 4.5:")
        print("=" * 60)
        print(answer)
        print("=" * 60)
        
        return answer
        
    except Exception as e:
        print(f"\n✗ An error occurred: {e}")
        raise


if __name__ == "__main__":
    main()
