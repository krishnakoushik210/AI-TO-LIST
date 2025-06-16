from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import openai
import os
import json
import random
from datetime import datetime, timedelta

# Set OpenAI API key directly
openai.api_key = "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"

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

used_time_slots = {
    'sleep': set(),
    'nap': set(),
    'breakfast': set(),
    'lunch': set(),
    'dinner': set(),
    'exercise': set(),
    'study': set(),
    'work': set(),
    'shopping': set(),
    'entertainment': set()
}

def get_unique_time_slot(activity, time_of_day, activity_times):
    """Get a unique time slot that hasn't been used recently."""
    if activity in activity_times and time_of_day in activity_times[activity]:
        available_times = [t for t in activity_times[activity][time_of_day] if t not in used_time_slots[activity]]
        if available_times:
            selected_time = random.choice(available_times)
            used_time_slots[activity].add(selected_time)
            # Keep only last 5 used times to allow reuse after a while
            used_time_slots[activity] = set(list(used_time_slots[activity])[-5:])
            return selected_time
    return None

def analyze_task(task):
    """Analyze a task using OpenAI API."""
    if not task or not isinstance(task, str):
        return jsonify({
            'category': 'Error',
            'start_time': 'N/A',
            'end_time': 'N/A',
            'priority': '📅 Schedule',
            'type': 'Routine',
            'rationale': 'Invalid task input'
        })

    try:
        # First try OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": """You are a task analyzer. For each task, provide:
                1. Category (Work, Personal, Health, etc.)
                2. Start time and end time (in 12-hour format)
                3. Priority (⚡ High, 📅 Schedule, ⏳ Low)
                4. Type (Routine, Critical, Optional, etc.)
                5. Rationale for the time slot
                Return the response in JSON format with these exact keys: category, start_time, end_time, priority, type, rationale."""},
                {"role": "user", "content": f"Analyze this task and provide start/end times: {task}"}
            ]
        )
        analysis = response.choices[0].message.content
        try:
            # Try to parse the analysis as JSON
            analysis_dict = json.loads(analysis)
            # Validate required fields
            required_fields = ['category', 'start_time', 'end_time', 'priority', 'type', 'rationale']
            for field in required_fields:
                if field not in analysis_dict:
                    analysis_dict[field] = get_default_value(field)
            return jsonify(analysis_dict)
        except json.JSONDecodeError:
            # If analysis is not JSON, use it as rationale
            return jsonify({
                'category': 'Uncategorized',
                'start_time': 'No start time',
                'end_time': 'No end time',
                'priority': '📅 Schedule',
                'type': 'Routine',
                'rationale': analysis
            })
    except Exception as e:
        print(f"Error analyzing task: {str(e)}")
        # Fallback to keyword-based analysis
        return jsonify(analyze_task_keywords(task))

def get_default_value(field):
    """Get default value for a field."""
    defaults = {
        'category': 'Uncategorized',
        'start_time': 'No start time',
        'end_time': 'No end time',
        'priority': '📅 Schedule',
        'type': 'Routine',
        'rationale': 'No rationale provided'
    }
    return defaults.get(field, 'N/A')

def analyze_task_keywords(task):
    """Analyze task using keyword matching."""
    task_lower = task.lower()
    
    # Enhanced category detection with more categories
    categories = {
        'Work': ['work', 'meeting', 'project', 'deadline', 'report', 'presentation', 'email', 'call'],
        'Shopping': ['shop', 'buy', 'grocery', 'store', 'market', 'purchase'],
        'Education': ['study', 'read', 'learn', 'class', 'course', 'homework', 'exam', 'test'],
        'Health': ['exercise', 'workout', 'gym', 'run', 'walk', 'yoga', 'meditation', 'doctor'],
        'Communication': ['call', 'email', 'message', 'chat', 'meet', 'talk', 'discuss'],
        'Rest': ['sleep', 'nap', 'rest', 'relax', 'bed', 'tired'],
        'Food': ['cook', 'eat', 'breakfast', 'lunch', 'dinner', 'snack', 'meal'],
        'Household': ['clean', 'wash', 'organize', 'tidy', 'laundry', 'dishes'],
        'Entertainment': ['play', 'game', 'watch', 'movie', 'music', 'read', 'hobby'],
        'Travel': ['travel', 'trip', 'journey', 'flight', 'drive', 'commute'],
        'Finance': ['pay', 'bill', 'budget', 'money', 'bank', 'finance'],
        'Social': ['party', 'event', 'gathering', 'meet', 'friend', 'family'],
        'Personal Care': ['bath', 'shower', 'groom', 'hygiene', 'self-care', 'skincare', 'hair']
    }
    
    # Find matching category
    category = 'Personal'  # default category
    for cat, keywords in categories.items():
        if any(keyword in task_lower for keyword in keywords):
            category = cat
            break
    
    # Enhanced time slot detection
    time_ranges = {
        'morning': (6, 11),    # 6 AM to 11 AM
        'afternoon': (12, 16), # 12 PM to 4 PM
        'evening': (17, 21),   # 5 PM to 9 PM
        'night': (22, 5)       # 10 PM to 5 AM
    }
    
    # Activity-specific time slots with variations
    activity_times = {
        'sleep': {
            'night': {
                'start': ['10:00 PM', '10:30 PM', '11:00 PM'],
                'end': ['6:00 AM', '6:30 AM', '7:00 AM']
            }
        },
        'nap': {
            'afternoon': {
                'start': ['1:00 PM', '1:30 PM', '2:00 PM'],
                'end': ['2:00 PM', '2:30 PM', '3:00 PM']
            }
        },
        'breakfast': {
            'morning': {
                'start': ['7:00 AM', '7:30 AM', '8:00 AM'],
                'end': ['7:30 AM', '8:00 AM', '8:30 AM']
            }
        },
        'lunch': {
            'afternoon': {
                'start': ['12:00 PM', '12:30 PM', '1:00 PM'],
                'end': ['1:00 PM', '1:30 PM', '2:00 PM']
            }
        },
        'dinner': {
            'evening': {
                'start': ['6:00 PM', '6:30 PM', '7:00 PM'],
                'end': ['7:00 PM', '7:30 PM', '8:00 PM']
            }
        },
        'exercise': {
            'morning': {
                'start': ['6:00 AM', '7:00 AM', '8:00 AM'],
                'end': ['7:00 AM', '8:00 AM', '9:00 AM']
            },
            'evening': {
                'start': ['5:00 PM', '6:00 PM', '7:00 PM'],
                'end': ['6:00 PM', '7:00 PM', '8:00 PM']
            }
        },
        'study': {
            'morning': {
                'start': ['9:00 AM', '10:00 AM', '11:00 AM'],
                'end': ['11:00 AM', '12:00 PM', '1:00 PM']
            },
            'afternoon': {
                'start': ['2:00 PM', '3:00 PM', '4:00 PM'],
                'end': ['4:00 PM', '5:00 PM', '6:00 PM']
            },
            'evening': {
                'start': ['7:00 PM', '8:00 PM', '9:00 PM'],
                'end': ['9:00 PM', '10:00 PM', '11:00 PM']
            }
        },
        'work': {
            'morning': {
                'start': ['9:00 AM', '10:00 AM'],
                'end': ['12:00 PM', '1:00 PM']
            },
            'afternoon': {
                'start': ['2:00 PM', '3:00 PM'],
                'end': ['5:00 PM', '6:00 PM']
            }
        },
        'shopping': {
            'morning': {
                'start': ['10:00 AM', '11:00 AM'],
                'end': ['11:00 AM', '12:00 PM']
            },
            'afternoon': {
                'start': ['3:00 PM', '4:00 PM'],
                'end': ['4:00 PM', '5:00 PM']
            },
            'evening': {
                'start': ['6:00 PM', '7:00 PM'],
                'end': ['7:00 PM', '8:00 PM']
            }
        },
        'entertainment': {
            'evening': {
                'start': ['8:00 PM', '9:00 PM', '10:00 PM'],
                'end': ['10:00 PM', '11:00 PM', '12:00 AM']
            }
        },
        'bath': {
            'morning': {
                'start': ['7:00 AM', '7:30 AM', '8:00 AM'],
                'end': ['7:30 AM', '8:00 AM', '8:30 AM']
            },
            'evening': {
                'start': ['8:00 PM', '8:30 PM', '9:00 PM'],
                'end': ['8:30 PM', '9:00 PM', '9:30 PM']
            }
        }
    }
    
    # Determine time of day based on activity
    time_of_day = 'morning'  # default for personal care
    if any(word in task_lower for word in ['nap', 'rest']):
        time_of_day = 'afternoon'
    elif any(word in task_lower for word in ['breakfast', 'morning']):
        time_of_day = 'morning'
    elif any(word in task_lower for word in ['lunch', 'noon', 'afternoon']):
        time_of_day = 'afternoon'
    elif any(word in task_lower for word in ['dinner', 'evening', 'night']):
        time_of_day = 'evening'
    elif any(word in task_lower for word in ['bath', 'shower']):
        time_of_day = 'evening' if 'night' in task_lower or 'evening' in task_lower else 'morning'
    
    # Get random time for the activity
    start_time = 'No start time'
    end_time = 'No end time'
    
    # Special handling for sleep tasks
    if 'sleep' in task_lower:
        sleep_times = activity_times['sleep']['night']
        if not hasattr(analyze_task_keywords, 'used_sleep_times'):
            analyze_task_keywords.used_sleep_times = set()
        
        available_start_times = [t for t in sleep_times['start'] if t not in analyze_task_keywords.used_sleep_times]
        
        if not available_start_times:
            analyze_task_keywords.used_sleep_times.clear()
            available_start_times = sleep_times['start']
        
        start_time = random.choice(available_start_times)
        end_time = random.choice(sleep_times['end'])
        analyze_task_keywords.used_sleep_times.add(start_time)
        
        if len(analyze_task_keywords.used_sleep_times) > 5:
            analyze_task_keywords.used_sleep_times = set(list(analyze_task_keywords.used_sleep_times)[-5:])
    else:
        # Handle other activities
        for activity, times in activity_times.items():
            if activity in task_lower or (activity == 'bath' and any(word in task_lower for word in ['bath', 'shower'])):
                if time_of_day in times:
                    start_time = random.choice(times[time_of_day]['start'])
                    end_time = random.choice(times[time_of_day]['end'])
                break
    
    # If no specific time found, generate random times based on time of day
    if start_time == 'No start time':
        start_hour, end_hour = time_ranges[time_of_day]
        random_start_hour = random.randint(start_hour, end_hour - 1)
        random_end_hour = random.randint(random_start_hour + 1, end_hour)
        random_minute = random.choice([0, 15, 30, 45])
        start_time = f"{random_start_hour:02d}:{random_minute:02d} {'AM' if random_start_hour < 12 else 'PM'}"
        end_time = f"{random_end_hour:02d}:{random_minute:02d} {'AM' if random_end_hour < 12 else 'PM'}"
    
    # Determine priority based on task characteristics
    priority = '📅 Schedule'
    if any(word in task_lower for word in ['urgent', 'important', 'deadline', 'due', 'asap']):
        priority = '⚡ High Priority'
    elif any(word in task_lower for word in ['optional', 'maybe', 'if time', 'when possible']):
        priority = '⏳ Low Priority'
    
    # Determine task type
    task_type = 'Routine'
    if any(word in task_lower for word in ['urgent', 'important', 'critical']):
        task_type = 'Critical'
    elif any(word in task_lower for word in ['optional', 'maybe']):
        task_type = 'Optional'
    elif any(word in task_lower for word in ['daily', 'everyday']):
        task_type = 'Daily'
    elif any(word in task_lower for word in ['weekly', 'monthly']):
        task_type = 'Recurring'
    
    # Generate rationale
    rationale = f"This {category.lower()} task is scheduled for {time_of_day} to maintain a balanced daily routine."
    if 'sleep' in task_lower:
        rationale = f"Adequate sleep is essential for maintaining good health and productivity. Recommended sleep time is from {start_time} to {end_time}."
    elif 'nap' in task_lower:
        rationale = f"A short nap can help improve alertness and performance. Best taken from {start_time} to {end_time}."
    elif 'exercise' in task_lower:
        rationale = f"Regular exercise helps maintain physical and mental well-being. Scheduled from {start_time} to {end_time}."
    elif 'study' in task_lower or 'work' in task_lower:
        rationale = f"This time slot ({start_time} to {end_time}) is optimal for focused work and learning."
    elif any(word in task_lower for word in ['bath', 'shower']):
        rationale = f"Personal hygiene is important for health and well-being. Scheduled from {start_time} to {end_time}."
    
    return {
        'category': category,
        'start_time': start_time,
        'end_time': end_time,
        'priority': priority,
        'type': task_type,
        'rationale': rationale
    }

@app.route('/')
def index():
    """Serve the main page."""
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    """Analyze a task using OpenAI API."""
    try:
        data = request.get_json()
        if not data or 'task' not in data:
            return jsonify({
                'category': 'Error',
                'start_time': 'N/A',
                'end_time': 'N/A',
                'priority': '📅 Schedule',
                'type': 'Routine',
                'rationale': 'Invalid task input. Please provide a task description.'
            }), 400

        task = data['task']
        timing_preference = data.get('timing_preference', 'ai')
        custom_start_time = data.get('custom_start_time', '')
        custom_end_time = data.get('custom_end_time', '')

        # If custom timing is selected, use the provided times
        if timing_preference == 'custom' and custom_start_time and custom_end_time:
            return jsonify({
                'category': 'Custom Schedule',
                'start_time': custom_start_time,
                'end_time': custom_end_time,
                'priority': '📅 Schedule',
                'type': 'Custom',
                'rationale': 'Using custom time schedule provided by user.'
            })

        # Otherwise, use AI analysis
        analysis = analyze_task_keywords(task)
        return jsonify(analysis)

    except Exception as e:
        print(f"Error analyzing task: {str(e)}")
        return jsonify({
            'category': 'Error',
            'start_time': 'N/A',
            'end_time': 'N/A',
            'priority': '📅 Schedule',
            'type': 'Routine',
            'rationale': f'Error analyzing task: {str(e)}'
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy"})

@app.route('/analyze_priorities', methods=['POST'])
def analyze_priorities():
    """Analyze tasks for priority matrix using OpenAI API."""
    try:
        data = request.get_json()
        tasks = data.get('tasks', [])
        print('DEBUG: Received tasks for priority analysis:', tasks)
        
        if not tasks:
            print('DEBUG: No tasks received.')
            return jsonify([])
            
        analyzed_tasks = []
        for task in tasks:
            # Get the task text
            task_text = task.get('text', '').lower()
            
            # Initialize importance and urgency
            importance = 'low'
            urgency = 'low'
            
            # Check for importance indicators
            importance_keywords = {
                'high': ['urgent', 'critical', 'important', 'deadline', 'meeting', 'client', 'project', 'presentation', 'report', 'exam', 'test', 'interview'],
                'medium': ['review', 'check', 'follow up', 'update', 'plan', 'schedule', 'prepare'],
                'low': ['optional', 'when possible', 'if time', 'leisure', 'hobby', 'entertainment']
            }
            
            # Check for urgency indicators
            urgency_keywords = {
                'high': ['urgent', 'asap', 'immediately', 'today', 'now', 'deadline', 'due', 'emergency', 'critical'],
                'medium': ['soon', 'this week', 'upcoming', 'next few days'],
                'low': ['whenever', 'sometime', 'no rush', 'flexible', 'optional']
            }
            
            # Determine importance
            for level, keywords in importance_keywords.items():
                if any(keyword in task_text for keyword in keywords):
                    importance = level
                    break
            
            # Determine urgency
            for level, keywords in urgency_keywords.items():
                if any(keyword in task_text for keyword in keywords):
                    urgency = level
                    break
            
            # Add time-based urgency
            if 'today' in task_text or 'now' in task_text:
                urgency = 'high'
            elif 'tomorrow' in task_text:
                urgency = 'medium'
            
            # Add context-based importance
            if any(word in task_text for word in ['meeting', 'client', 'project', 'deadline']):
                importance = 'high'
            
            # Create analyzed task object
            analyzed_task = {
                'id': task.get('id'),
                'text': task.get('text'),
                'importance': importance,
                'urgency': urgency,
                'analysis': task.get('analysis', {})
            }
            
            analyzed_tasks.append(analyzed_task)
        print('DEBUG: Returning analyzed tasks:', analyzed_tasks)
        return jsonify(analyzed_tasks)
        
    except Exception as e:
        print(f"Error analyzing priorities: {str(e)}")
        return jsonify([])

if __name__ == '__main__':
    app.run(debug=True, port=5000) 