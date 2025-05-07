from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import json
import os
from dotenv import load_dotenv
from flask_cors import CORS
import google.generativeai as genai
import base64
from components.scoringModel import predict_score, train_from_user_data, train_dummy_model


load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
has_valid_api_key = False

if api_key:
    try:
        genai.configure(api_key=api_key)
        has_valid_api_key = True
        print("Gemini API key configured successfully")
    except Exception as e:
        print(f"Error configuring Gemini API: {str(e)}")
        has_valid_api_key = False
else:
    print("WARNING: No GEMINI_API_KEY found in environment variables")
    has_valid_api_key = False

print("Initializing scoring model...")
try:
    if os.path.exists("components/score_model.pkl"):
        os.remove("components/score_model.pkl")
    train_dummy_model()
    print("Scoring model created successfully")
except Exception as e:
    print(f"Error creating scoring model: {str(e)}")

app = Flask(__name__)

# Configure CORS to be more specific in production
if os.getenv('RAILWAY_ENVIRONMENT') == 'production':
    # Get the frontend URL from environment
    frontend_url = os.getenv('FRONTEND_URL', '*')
    CORS(app, resources={r"/*": {"origins": frontend_url}})
else:
    # In development, allow all origins
    CORS(app)

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint to verify the app is running"""
    api_key_status = "available" if has_valid_api_key else "missing"
    return jsonify({
        "status": "healthy",
        "api_key": api_key_status,
        "environment": os.getenv('RAILWAY_ENVIRONMENT', 'development')
    })

@app.route('/demo-data', methods=['GET', 'POST'])
def demo_data():
    """Endpoint that returns demo data without requiring Gemini API"""
    return jsonify({
        "source": "Demo Data",
        "category": "E-commerce",
        "analysis": {
            "cta": {"observations": [
                "Multiple CTAs are present but lack visual distinction", 
                "The primary 'Buy Now' CTA is not visually prominent enough",
                "CTAs use generic wording rather than action-oriented text"
            ]},
            "visual_hierarchy": {"observations": [
                "Product images are well displayed but lack consistent sizing",
                "Important information like price and availability is not emphasized enough",
                "Navigation elements compete with product content for attention"
            ]},
            "copy_effectiveness": {"observations": [
                "Product descriptions are too technical and lack benefit-focused language",
                "Headers don't clearly communicate unique value propositions",
                "Too much text without proper formatting makes content hard to scan"
            ]},
            "trust_signals": {"observations": [
                "Customer reviews are present but not prominently displayed",
                "Missing trust badges and security indicators",
                "Return policy and guarantees are buried in footer text"
            ]}
        },
        "suggestions": {
            "cta": {
                "high_priority": [
                    "Redesign primary CTA with contrasting colors and increased size",
                    "Replace generic CTA text with specific action-oriented phrases"
                ],
                "additional": [
                    "Reduce the number of competing CTAs on each page",
                    "Add hover effects to make CTAs more interactive"
                ]
            },
            "visual_hierarchy": {
                "high_priority": [
                    "Standardize product image sizes and quality across the site",
                    "Use typography and color to emphasize key product information"
                ],
                "additional": [
                    "Simplify navigation to reduce competition with product content",
                    "Add more whitespace to improve content scannability"
                ]
            },
            "copy_effectiveness": {
                "high_priority": [
                    "Rewrite product descriptions to focus on benefits rather than specifications",
                    "Create compelling headers that highlight unique selling points"
                ],
                "additional": [
                    "Break up text blocks with bullet points and subheadings",
                    "Add customer-centric language that addresses pain points"
                ]
            },
            "trust_signals": {
                "high_priority": [
                    "Add security badges and payment icons near checkout CTAs",
                    "Feature customer reviews more prominently on product pages"
                ],
                "additional": [
                    "Create a dedicated guarantees section above the footer",
                    "Add social proof elements like 'X customers purchased this week'"
                ]
            }
        },
        "website_score": 65.5
    })

def fetch_website_content(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        raise Exception(f"Error fetching website: {str(e)}")

def determine_website_category(content):
    """Use Gemini API to determine website category."""
    if not has_valid_api_key:
        return "Unknown (Demo Mode)"
        
    try:
        limited_content = content[:2000]
        model = genai.GenerativeModel('gemini-2.0-flash')
        prompt = f"""
        You are an expert web analyst. Identify the most likely category of this website.
        
        Based on this website content, determine the category (e.g. e-commerce, blog, SaaS, portfolio, etc.):
        
        {limited_content}
        
        Return ONLY the category name, nothing else.
        """
        
        response = model.generate_content(prompt)
        
        category = response.text.strip()
        return category
    except Exception as e:
        print(f"Error determining website category: {str(e)}")
        return "Unknown (API Error)"

def extract_website_components(content, category):
    """Use Gemini API to extract website components and evaluate them."""
    if not has_valid_api_key:
        return {
            "cta": {"observations": [
                "Multiple CTAs are present but lack visual distinction", 
                "The primary CTA is not visually prominent enough",
                "CTAs use generic wording rather than action-oriented text"
            ]},
            "visual_hierarchy": {"observations": [
                "Content lacks clear visual hierarchy",
                "Important information is not emphasized enough",
                "Layout elements compete for attention"
            ]},
            "copy_effectiveness": {"observations": [
                "Content is too technical and lacks benefit-focused language",
                "Headers don't clearly communicate value propositions",
                "Too much text without proper formatting makes content hard to scan"
            ]},
            "trust_signals": {"observations": [
                "Trust indicators are not prominently displayed",
                "Missing trust badges and security indicators",
                "Social proof elements are insufficient"
            ]}
        }

    try:
        limited_content = content[:3000]
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        prompt = f"""
        You are an expert web analyst specializing in UX and conversion optimization.
        
        Analyze this {category} website content and extract the following components:
        
        1. CTA (Call to Action): Identify all CTAs and evaluate their effectiveness.
        2. Visual Hierarchy: Analyze how content is visually prioritized and structured.
        3. Copy Effectiveness: Evaluate the quality, clarity and persuasiveness of the text.
        4. Trust Signals: Identify elements that build trust (testimonials, certifications, etc).
        
        For each category, provide detailed observations. If any component is missing, note this as well.
        
        Format your response as JSON with the following structure:
        {{
            "cta": {{ "observations": [list of findings as simple strings] }},
            "visual_hierarchy": {{ "observations": [list of findings as simple strings] }},
            "copy_effectiveness": {{ "observations": [list of findings as simple strings] }},
            "trust_signals": {{ "observations": [list of findings as simple strings] }}
        }}
        
        Website content:
        {limited_content}
        
        Respond with ONLY the properly formatted JSON, nothing else. Each observation must be a simple string, not an object.
        """
        
        response = model.generate_content(prompt)
        
        try:
            analysis = json.loads(response.text)
        except json.JSONDecodeError:
            text = response.text
            start_idx = text.find('{')
            end_idx = text.rfind('}') + 1
            if start_idx >= 0 and end_idx > start_idx:
                json_str = text[start_idx:end_idx]
                analysis = json.loads(json_str)
            else:
                analysis = {
                    "cta": {"observations": ["Unable to analyze CTAs"]},
                    "visual_hierarchy": {"observations": ["Unable to analyze visual hierarchy"]},
                    "copy_effectiveness": {"observations": ["Unable to analyze copy"]},
                    "trust_signals": {"observations": ["Unable to analyze trust signals"]}
                }
                
        return analysis
    except Exception as e:
        print(f"Error extracting website components: {str(e)}")
        return {
            "cta": {"observations": ["Error analyzing CTAs: API unavailable"]},
            "visual_hierarchy": {"observations": ["Error analyzing visual hierarchy: API unavailable"]},
            "copy_effectiveness": {"observations": ["Error analyzing copy: API unavailable"]},
            "trust_signals": {"observations": ["Error analyzing trust signals: API unavailable"]}
        }

def generate_suggestions(analysis, category):
    """Generate prioritized improvement suggestions based on analysis."""
    if not has_valid_api_key:
        return {
            "cta": {
                "high_priority": [
                    "Redesign primary CTA with contrasting colors and increased size",
                    "Replace generic CTA text with specific action-oriented phrases"
                ],
                "additional": [
                    "Reduce the number of competing CTAs on each page",
                    "Add hover effects to make CTAs more interactive"
                ]
            },
            "visual_hierarchy": {
                "high_priority": [
                    "Establish clear visual hierarchy with size, color, and spacing",
                    "Use typography and color to emphasize key information"
                ],
                "additional": [
                    "Simplify layout to reduce visual competition",
                    "Add more whitespace to improve content scannability"
                ]
            },
            "copy_effectiveness": {
                "high_priority": [
                    "Focus content on benefits rather than technical specifications",
                    "Create compelling headers that highlight unique selling points"
                ],
                "additional": [
                    "Break up text blocks with bullet points and subheadings",
                    "Add customer-centric language that addresses pain points"
                ]
            },
            "trust_signals": {
                "high_priority": [
                    "Add security badges and verification icons in visible locations",
                    "Feature testimonials or reviews more prominently"
                ],
                "additional": [
                    "Display guarantees and policies more visibly",
                    "Add social proof elements throughout the site"
                ]
            }
        }
        
    try:
        analysis_json = json.dumps(analysis)
        
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        prompt = f"""
        You are an expert conversion rate optimization consultant known for providing actionable suggestions.
        
        Based on this analysis of a {category} website:
        
        {analysis_json}
        
        Generate specific, actionable improvement suggestions for each component (CTA, Visual Hierarchy, Copy Effectiveness, Trust Signals).
        
        For each component:
        1. Provide at least 3 specific suggestions
        2. Rank each suggestion by impact potential (high, medium, low)
        3. Mark the 2 highest impact suggestions for each component
        
        Format your response as JSON with the following structure:
        {{
            "cta": {{
                "high_priority": [2 highest impact suggestions as simple strings],
                "additional": [remaining suggestions as simple strings]
            }},
            "visual_hierarchy": {{
                "high_priority": [2 highest impact suggestions as simple strings],
                "additional": [remaining suggestions as simple strings]
            }},
            "copy_effectiveness": {{
                "high_priority": [2 highest impact suggestions as simple strings],
                "additional": [remaining suggestions as simple strings]
            }},
            "trust_signals": {{
                "high_priority": [2 highest impact suggestions as simple strings],
                "additional": [remaining suggestions as simple strings]
            }}
        }}
        
        IMPORTANT: Each suggestion MUST be a simple string, not an object. Do not include impact ratings inside the arrays.
        
        Respond with ONLY the properly formatted JSON, nothing else.
        """
        
        response = model.generate_content(prompt)
        
        try:
            suggestions = json.loads(response.text)
        except json.JSONDecodeError:
            text = response.text
            start_idx = text.find('{')
            end_idx = text.rfind('}') + 1
            if start_idx >= 0 and end_idx > start_idx:
                json_str = text[start_idx:end_idx]
                suggestions = json.loads(json_str)
            else:
                suggestions = {
                    "cta": {
                        "high_priority": ["Improve CTA visibility", "Make CTA messaging more compelling"],
                        "additional": ["Test different CTA colors"]
                    },
                    "visual_hierarchy": {
                        "high_priority": ["Improve content organization", "Enhance key element visibility"],
                        "additional": ["Add more whitespace between sections"]
                    },
                    "copy_effectiveness": {
                        "high_priority": ["Clarify value proposition", "Make headlines more compelling"],
                        "additional": ["Simplify complex sentences"]
                    },
                    "trust_signals": {
                        "high_priority": ["Add customer testimonials", "Display security badges"],
                        "additional": ["Include company credentials or awards"]
                    }
                }
        for section in suggestions:
            if 'high_priority' in suggestions[section]:
                suggestions[section]['high_priority'] = [
                    str(item) if not isinstance(item, str) else item 
                    for item in suggestions[section]['high_priority']
                ]
            
            if 'additional' in suggestions[section]:
                suggestions[section]['additional'] = [
                    str(item) if not isinstance(item, str) else item 
                    for item in suggestions[section]['additional']
                ]
                
        return suggestions
    except Exception as e:
        print(f"Error generating suggestions: {str(e)}")
        return {
            "cta": {
                "high_priority": ["Improve CTA visibility", "Make CTA messaging more compelling"],
                "additional": ["Test different CTA colors"]
            },
            "visual_hierarchy": {
                "high_priority": ["Improve content organization", "Enhance key element visibility"],
                "additional": ["Add more whitespace between sections"]
            },
            "copy_effectiveness": {
                "high_priority": ["Clarify value proposition", "Make headlines more compelling"],
                "additional": ["Simplify complex sentences"]
            },
            "trust_signals": {
                "high_priority": ["Add customer testimonials", "Display security badges"],
                "additional": ["Include company credentials or awards"]
            }
        }

@app.route('/components', methods=['POST'])
def analyze_website():
    """Main route to analyze a website from URL or HTML."""
    try:
        # If API key is missing and not in demo mode, redirect to demo-data
        if not has_valid_api_key:
            print("No valid API key, returning demo data")
            return demo_data()
            
        data = request.json

        if 'url' in data:
            content = fetch_website_content(data['url'])
            source = data['url']

            soup = BeautifulSoup(content, 'html.parser')
            for script in soup(["script", "style"]):
                script.extract()
            text_content = soup.get_text(separator=" ", strip=True)

            website_score = predict_score(html=content)
            
            return process_text_content(text_content, source, website_score)
        elif 'html' in data:
            content = data['html']
            source = "HTML input"

            soup = BeautifulSoup(content, 'html.parser')
            for script in soup(["script", "style"]):
                script.extract()
            text_content = soup.get_text(separator=" ", strip=True)

            website_score = predict_score(html=content)
            
            return process_text_content(text_content, source, website_score)
        elif 'image' in data:

            image_data = data['image']
            if ';base64,' in image_data:

                image_data = image_data.split(';base64,')[1]

            image_parts = [{"mime_type": "image/jpeg", "data": image_data}]
            
            website_score = None  
            
            return process_image_content(image_parts, "Image input", website_score)
        else:
            return jsonify({"error": "Either URL, HTML, or image is required"}), 400
    
    except Exception as e:
        print(f"Error in analyze_website: {str(e)}")
        return jsonify({"error": str(e), "fallback": "Using demo data due to error", "demo": True}), 200

def process_text_content(text_content, source, website_score=None):
    """Process text content for analysis"""

    category = determine_website_category(text_content)
    
    components_analysis = extract_website_components(text_content, category)
    
    suggestions = generate_suggestions(components_analysis, category)
    
    result = {
        "source": source,
        "category": category,
        "analysis": components_analysis,
        "suggestions": suggestions,
        "website_score": website_score
    }
    
    return jsonify(result)

def process_image_content(image_parts, source, website_score=None):
    """Process image content for analysis"""
    if not has_valid_api_key:
        # Return demo data for image analysis
        return jsonify({
            "source": "Image input (Demo Mode)",
            "category": "E-commerce",
            "analysis": {
                "cta": {"observations": [
                    "Multiple CTAs are present but lack visual distinction", 
                    "The primary 'Buy Now' CTA is not visually prominent enough",
                    "CTAs use generic wording rather than action-oriented text"
                ]},
                "visual_hierarchy": {"observations": [
                    "Product images are well displayed but lack consistent sizing",
                    "Important information like price and availability is not emphasized enough",
                    "Navigation elements compete with product content for attention"
                ]},
                "copy_effectiveness": {"observations": [
                    "Product descriptions are too technical and lack benefit-focused language",
                    "Headers don't clearly communicate unique value propositions",
                    "Too much text without proper formatting makes content hard to scan"
                ]},
                "trust_signals": {"observations": [
                    "Customer reviews are present but not prominently displayed",
                    "Missing trust badges and security indicators",
                    "Return policy and guarantees are buried in footer text"
                ]}
            },
            "suggestions": {
                "cta": {
                    "high_priority": [
                        "Redesign primary CTA with contrasting colors and increased size",
                        "Replace generic CTA text with specific action-oriented phrases"
                    ],
                    "additional": [
                        "Reduce the number of competing CTAs on each page",
                        "Add hover effects to make CTAs more interactive"
                    ]
                },
                "visual_hierarchy": {
                    "high_priority": [
                        "Standardize product image sizes and quality across the site",
                        "Use typography and color to emphasize key product information"
                    ],
                    "additional": [
                        "Simplify navigation to reduce competition with product content",
                        "Add more whitespace to improve content scannability"
                    ]
                },
                "copy_effectiveness": {
                    "high_priority": [
                        "Rewrite product descriptions to focus on benefits rather than specifications",
                        "Create compelling headers that highlight unique selling points"
                    ],
                    "additional": [
                        "Break up text blocks with bullet points and subheadings",
                        "Add customer-centric language that addresses pain points"
                    ]
                },
                "trust_signals": {
                    "high_priority": [
                        "Add security badges and payment icons near checkout CTAs",
                        "Feature customer reviews more prominently on product pages"
                    ],
                    "additional": [
                        "Create a dedicated guarantees section above the footer",
                        "Add social proof elements like 'X customers purchased this week'"
                    ]
                }
            },
            "website_score": 68.5,
            "demo": True
        })
        
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        mime_type = image_parts[0]['mime_type']
        image_data = image_parts[0]['data']
        
        image_part = {
            "inline_data": {
                "mime_type": mime_type,
                "data": image_data
            }
        }
# env update
        category_prompt = "You are an expert web analyst. Identify the most likely category of this website screenshot (e.g. e-commerce, blog, SaaS, portfolio, etc.). Return ONLY the category name, nothing else."
        category_response = model.generate_content([category_prompt, image_part])
        category = category_response.text.strip()
        
        components_prompt = f"""
        You are an expert web analyst specializing in UX and conversion optimization.
        
        Analyze this {category} website screenshot and extract the following components:
        
        1. CTA (Call to Action): Identify all CTAs and evaluate their effectiveness.
        2. Visual Hierarchy: Analyze how content is visually prioritized and structured.
        3. Copy Effectiveness: Evaluate the quality, clarity and persuasiveness of the text.
        4. Trust Signals: Identify elements that build trust (testimonials, certifications, etc).
        
        For each category, provide detailed observations. If any component is missing, note this as well.
        
        Format your response as JSON with the following structure:
        {{
            "cta": {{ "observations": [list of findings as simple strings] }},
            "visual_hierarchy": {{ "observations": [list of findings as simple strings] }},
            "copy_effectiveness": {{ "observations": [list of findings as simple strings] }},
            "trust_signals": {{ "observations": [list of findings as simple strings] }}
        }}
        
        Respond with ONLY the properly formatted JSON, nothing else. Each observation must be a simple string, not an object.
        """
        
        components_response = model.generate_content([components_prompt, image_part])
        
        try:
            analysis = json.loads(components_response.text)
        except json.JSONDecodeError:
            text = components_response.text
            start_idx = text.find('{')
            end_idx = text.rfind('}') + 1
            if start_idx >= 0 and end_idx > start_idx:
                json_str = text[start_idx:end_idx]
                analysis = json.loads(json_str)
            else:
               
                analysis = {
                    "cta": {"observations": ["Unable to analyze CTAs from image"]},
                    "visual_hierarchy": {"observations": ["Unable to analyze visual hierarchy from image"]},
                    "copy_effectiveness": {"observations": ["Unable to analyze copy from image"]},
                    "trust_signals": {"observations": ["Unable to analyze trust signals from image"]}
                }
        
        suggestions = generate_suggestions(analysis, category)
        
        total_observations = sum(len(analysis[key]['observations']) for key in analysis)
        positive_observations = 0
        negative_observations = 0
        for section in analysis:
            for observation in analysis[section]['observations']:
                lower_obs = observation.lower()
                if "unable to analyze" in lower_obs:
                    continue
                if any(term in lower_obs for term in ["missing", "lack", "no ", "poor", "weak", "confusing", "unclear", 
                                                     "ineffective", "absent", "could be", "should be", "not"]):
                    negative_observations += 1
                elif any(term in lower_obs for term in ["clear", "effective", "good", "strong", "well", "present", 
                                                      "prominent", "visible", "professional"]):
                    positive_observations += 1
        informative_observations = positive_observations + negative_observations
        if informative_observations > 0:
            image_based_score = 50 + (30 * (positive_observations / informative_observations - 0.5))
            image_based_score = min(100, max(0, image_based_score))
        else:
            image_based_score = 50
        website_score = image_based_score

        result = {
            "source": source,
            "category": category,
            "analysis": analysis,
            "suggestions": suggestions,
            "website_score": website_score
        }
        
        return jsonify(result)
    except Exception as e:
        print(f"Error processing image: {str(e)}")
        # Return demo data in case of error
        return jsonify({
            "source": "Image input (Error Fallback)",
            "category": "Website",
            "analysis": {
                "cta": {"observations": ["Unable to analyze CTAs from image due to API error"]},
                "visual_hierarchy": {"observations": ["Unable to analyze visual hierarchy from image due to API error"]},
                "copy_effectiveness": {"observations": ["Unable to analyze copy from image due to API error"]},
                "trust_signals": {"observations": ["Unable to analyze trust signals from image due to API error"]}
            },
            "suggestions": {
                "cta": {
                    "high_priority": ["Add clear call-to-action buttons", "Make CTAs visually distinct"],
                    "additional": ["Use action-oriented text in CTAs"]
                },
                "visual_hierarchy": {
                    "high_priority": ["Improve content organization", "Use consistent visual elements"],
                    "additional": ["Add proper spacing between elements"]
                },
                "copy_effectiveness": {
                    "high_priority": ["Simplify and clarify messaging", "Focus on benefits"],
                    "additional": ["Use short, scannable content"]
                },
                "trust_signals": {
                    "high_priority": ["Add testimonials or reviews", "Display trust badges"],
                    "additional": ["Make security information visible"]
                }
            },
            "website_score": 50,
            "demo": True,
            "error": str(e)
        })

@app.route('/train-model', methods=['POST'])
def train_scoring_model():
    """Endpoint to train the scoring model with user data and feedback"""
    if not has_valid_api_key:
        return jsonify({
            "success": True,
            "message": "Model training skipped (Demo Mode)",
            "old_score": 50.0,
            "new_score": 50.0,
            "model_updated": False,
            "demo": True
        })
        
    try:
        data = request.json
        
        if not data or 'html' not in data or 'user_score' not in data:
            return jsonify({"error": "Missing required fields: html and user_score"}), 400
        
        html = data['html']
        user_score = float(data['user_score'])

        user_feedback = data.get('user_feedback', {})

        result = train_from_user_data(html, user_score, user_feedback)
        
        return jsonify({
            "success": True,
            "message": "Model trained successfully",
            "old_score": result["old_score"],
            "new_score": result["new_score"],
            "model_updated": result["model_updated"]
        })
        
    except Exception as e:
        print(f"Error training model: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Error training model, but service remains available",
            "old_score": 50.0,
            "new_score": 50.0,
            "model_updated": False
        }), 200  # Return 200 to keep the service working

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5050))
    app.run(host="0.0.0.0", port=port, debug=(os.getenv('RAILWAY_ENVIRONMENT') != 'production'))
