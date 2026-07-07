import boto3


def generate(
    prompt: str,
    model_id: str,
    region: str,
    system: str = "",
    history: list[dict] = [],
) -> str:
    """Call Claude on Amazon Bedrock and return the response text.

    Args:
        prompt:   User message text to send (appended after history).
        model_id: Bedrock model ID or inference profile ID.
        region:   AWS region where the Bedrock endpoint is hosted.
        system:   System prompt passed outside of messages — sets the
                  model's persona, constraints, or output format for the
                  entire conversation. Omitted when empty.
        history:  Prior conversation turns in
                  [{"role": "user"|"assistant", "content": "..."}] format.
                  These are prepended before prompt so the model has
                  context of what was said earlier. Omitted when empty.

    Returns:
        The assistant's reply as a plain string.
    """
    client = boto3.client("bedrock-runtime", region_name=region)

    # Build the message list: history first, then the new user turn.
    messages = [
        {
            "role": turn["role"],       # role: "user" or "assistant"
            "content": [{"text": turn["content"]}],  # contentText: turn body
        }
        for turn in history
    ] + [
        {
            "role": "user",
            "content": [{"text": prompt}],  # contentText: the current prompt
        }
    ]

    kwargs = {
        "modelId": model_id,
        "messages": messages,
        "inferenceConfig": {
            "maxTokens": 1024,  # max_tokens: upper bound on generated output tokens
        },
    }

    # system: passed as a top-level field, not inside messages.
    # Controls model behaviour for the whole conversation.
    if system:
        kwargs["system"] = [{"text": system}]

    response = client.converse(**kwargs)

    return response["output"]["message"]["content"][0]["text"]
