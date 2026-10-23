import pickle
import os
import ocr

script_dir = os.path.dirname(__file__)
abs_file_path = os.path.join(script_dir, "tf_idf.pkl")

with open(abs_file_path, 'rb') as f:
    vect, model, le = pickle.load(f)

# Function to predict a single question
def predict_topic(question_text):
    """
    Predict the topic_id for a single question.
    
    Args:
        question_text: The question content as a string
    
    Returns:
        topic_id: The predicted topic ID
    """
    # Transform the text using the vectorizer
    question_vectorized = vect.transform([question_text])
    
    # Predict using the model
    prediction_encoded = model.predict(question_vectorized)[0]
    
    # Decode back to original topic_id
    topic_id = le.inverse_transform([prediction_encoded])[0]
    
    return topic_id

# Function to get prediction with probability
def predict_topic_with_confidence(question_text):
    """
    Predict topic with confidence scores.
    
    Args:
        question_text: The question content as a string
    
    Returns:
        dict: Prediction result with confidence
    """
    # Transform the text
    question_vectorized = vect.transform([question_text])
    
    # Get prediction
    prediction_encoded = model.predict(question_vectorized)[0]
    topic_id = le.inverse_transform([prediction_encoded])[0]
    
    # Get probabilities (if model supports it)
    if hasattr(model, 'predict_proba'):
        probabilities = model.predict_proba(question_vectorized)[0]
        confidence = probabilities[prediction_encoded] * 100
        
        # Get top 3 predictions
        top_3_indices = probabilities.argsort()[-3:][::-1]
        top_3_topics = le.inverse_transform(top_3_indices)
        top_3_probs = probabilities[top_3_indices] * 100
        
        return {
            'topic_id': topic_id,
            'confidence': confidence,
            'top_3': list(zip(top_3_topics, top_3_probs))
        }
    else:
        return {
            'topic_id': topic_id,
            'confidence': None,
            'top_3': None
        }


# Example usage
if __name__ == "__main__":
    ocr.__init__()
    print("Interactive Mode - Enter your own questions!")
    print("(Type 'quit' to exit)")
    print("="*60)
    
    while True:
        user_input = input("\nEnter question: ").strip()
        
        if user_input.lower() == 'quit':
            print("Goodbye!")
            break
        
        if not user_input:
            print("Please enter a question.")
            continue
        
        user_input = ocr.stemm_text(ocr.clean_string(user_input))
        result = predict_topic_with_confidence(user_input)
        print(f"\n✓ Predicted Topic ID: {result['topic_id']}")
        
        if result['confidence'] is not None:
            print(f"  Confidence: {result['confidence']:.2f}%")