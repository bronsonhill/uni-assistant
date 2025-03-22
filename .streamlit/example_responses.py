def get_bot_response(user_input, module):
    """Get a response from the tutor bot and track competencies using function calling"""
    try:
        client = setup_openai_client()
        module_context, module_name = get_module_content(module)
        
        # Get system prompt
        system_prompt = load_tutor_prompt()
        
        # Define the competency management tools
        tools = [
            {
                "type": "function",
                "name": "update_topic_competency",
                "description": "Update a student's competency level for a specific topic",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "topic_name": {
                            "type": "string",
                            "description": "The name of the topic to update"
                        },
                        "level": {
                            "type": "integer",
                            "description": "Competency level (0=not started, 1=in progress, 2=completed)",
                            "enum": [0, 1, 2]
                        },
                        "reason": {
                            "type": "string",
                            "description": "Brief explanation for the competency update"
                        }
                    },
                    "required": ["topic_name", "level", "reason"]
                }
            },
            {
                "type": "function",
                "name": "get_topic_competency",
                "description": "Get a student's current competency level for a specific topic",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "topic_name": {
                            "type": "string",
                            "description": "The name of the topic to check"
                        }
                    },
                    "required": ["topic_name"]
                }
            }
        ]
        
        # Get previous response ID from session state for this module
        chat_history_key = f"messages_module_{module}"
        previous_response_id = None
        
        # Get the last response ID from the chat history
        if chat_history_key in st.session_state:
            for message in reversed(st.session_state[chat_history_key]):
                if message.get("role") == "assistant" and message.get("response_id"):
                    previous_response_id = message.get("response_id")
                    break
        
        # Prepare input content
        input_content = []
        
        # Check if this is the first user message
        is_first_message = chat_history_key in st.session_state and len(st.session_state[chat_history_key]) <= 3
        
        # If this is the first message and there's a file, include it first
        if is_first_message:
            file_id = st.session_state.get(f"module_{module}_file_id")
            if file_id:
                cleaned_file_id = clean_file_id(file_id)
                if cleaned_file_id:
                    input_content.append({
                        "role": "system",
                        "content": [{"type": "input_file", "file_id": cleaned_file_id}]
                    })
        
        # Add the current user message
        input_content.append({
            "role": "user",
            "content": user_input
        })
        
        # Call the OpenAI API with function definitions
        response = client.responses.create(
            model="gpt-4o",
            instructions=system_prompt,
            input=input_content,
            tools=tools,
            previous_response_id=previous_response_id
        )
        
        # Handle function calls if any
        if hasattr(response, 'output') and response.output and any(item.type == "function_call" for item in response.output):
            # Process function calls
            new_messages = list(input_content)  # Create a copy of input_content
            
            # For each function call in the output
            for tool_call in [item for item in response.output if item.type == "function_call"]:
                # Add the function call to messages
                new_messages.append(tool_call)
                
                # Process the function call
                func_name = tool_call.name
                func_args = json.loads(tool_call.arguments)
                
                # Handle different function types
                result = None
                if func_name == "update_topic_competency":
                    topic_name = func_args.get("topic_name")
                    level = func_args.get("level")
                    reason = func_args.get("reason")
                    
                    if topic_name is not None and level is not None:
                        # Update the competency in MongoDB
                        update_competency(
                            st.session_state.user_id,
                            topic_name,
                            level
                        )
                        
                        result = f"Successfully updated competency for {topic_name} to level {level}"
                        
                        if st.session_state.get("debug_mode", False):
                            st.write(f"Debug: Updated competency for topic {topic_name} to level {level}")
                            st.write(f"Debug: Reason: {reason}")
                
                elif func_name == "get_topic_competency":
                    topic_name = func_args.get("topic_name")
                    
                    if topic_name is not None:
                        # Get the competency from MongoDB
                        competency_data = get_topic_competency(
                            st.session_state.user_id,
                            topic_name
                        )
                        
                        if competency_data:
                            progress = competency_data.get("progress", 0)
                            # Progress is now directly the level (0, 1, 2)
                            result = json.dumps({
                                "topic_name": topic_name,
                                "progress": progress,
                                "level": progress
                            })
                        else:
                            result = f"No competency data found for {topic_name}"
                        
                        if st.session_state.get("debug_mode", False):
                            st.write(f"Debug: Retrieved competency for topic {topic_name}:", competency_data)
                
                # Add the function result to messages
                if result is not None:
                    new_messages.append({
                        "type": "function_call_output",
                        "call_id": tool_call.call_id,
                        "output": result
                    })
            
            try:
                # Generate a new response with the function results
                new_response = client.responses.create(
                    model="gpt-4o",
                    instructions=system_prompt,
                    input=new_messages
                )
                
                # Update the response
                response_text = new_response.output_text
                response = new_response
                
            except Exception as tool_error:
                # Log the error but continue with the original response
                st.error(f"Error handling function calls: {str(tool_error)}")
                if st.session_state.get("debug_mode", False):
                    st.exception(tool_error)
                    st.write("Debug - Messages:", new_messages)
        else:
            response_text = response.output_text
        
        # Store the response in chat history
        if chat_history_key not in st.session_state:
            st.session_state[chat_history_key] = []
        
        new_message = {
            "role": "assistant",
            "content": response_text,
            "response_id": response.id
        }
        st.session_state[chat_history_key].append(new_message)
        
        return response_text
        
    except Exception as e:
        st.error(f"Error generating response: {str(e)}")
        if st.session_state.get("debug_mode", False):
            st.exception(e)
        return "I'm sorry, I encountered an error. Please try again."