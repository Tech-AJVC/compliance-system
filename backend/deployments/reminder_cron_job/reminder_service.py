#!/usr/bin/env python3
"""
Reminder Service for Daily Cron Job
Runs daily to check for:
1. Capital call reminders (7th of each quarter)
2. Task due date reminders (3 days before)

📧 EMAIL PREVIEW MODE:
- Set PREVIEW_MODE = True to see email previews without sending
- Set PREVIEW_MODE = False to actually send emails
- HTML emails will be saved to /tmp/email_preview_*.html for browser viewing
"""

import os
import sys
import logging
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import List, Dict, Any

# Preview mode - set to True to see email previews instead of sending
PREVIEW_MODE = False

# Add parent directory to path for imports (since we're in reminder_cron_job folder)
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

# Configure logging (console only for Kubernetes pods)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Only console logging for K8s pods
    ]
)
logger = logging.getLogger(__name__)

# Import application dependencies (same as main app)
from app.models.compliance_task import ComplianceTask
from app.models.fund_details import FundDetails
from app.models.user import User
from app.utils.google_clients_gcp import gmail_send_email
from app.database.base import get_db
from sqlalchemy import cast, Date


def preview_email(subject: str, recipient: str, sender: str, body: str):
    """
    Display a preview of the email that would be sent
    """
    print("\n" + "=" * 80)
    print("📧 EMAIL PREVIEW")
    print("=" * 80)
    print(f"From: {sender}")
    print(f"To: {recipient}")
    print(f"Subject: {subject}")
    print("-" * 80)
    
    # Check if it's HTML content
    if body.strip().startswith('<html>') or '<div' in body or '<table' in body:
        print("Content-Type: text/html")
        print("-" * 80)
        
        # For HTML, show a simplified version
        import re
        # Remove HTML tags for a cleaner preview
        clean_text = re.sub('<[^<]+?>', '', body)
        # Clean up extra whitespace
        clean_text = re.sub(r'\n\s*\n', '\n\n', clean_text)
        clean_text = re.sub(r'  +', ' ', clean_text)
        
        print("HTML EMAIL (text preview):")
        print(clean_text[:1000] + "..." if len(clean_text) > 1000 else clean_text)
        
        # Optionally save HTML to file for browser viewing
        try:
            preview_file = f"/tmp/email_preview_{int(datetime.now().timestamp())}.html"
            with open(preview_file, 'w', encoding='utf-8') as f:
                f.write(body)
            print(f"\n💾 Full HTML saved to: {preview_file}")
            print("   You can open this file in a browser to see the full styled email")
        except Exception as e:
            print(f"Could not save HTML preview: {e}")
    else:
        print("Content-Type: text/plain")
        print("-" * 80)
        print(body[:1000] + "..." if len(body) > 1000 else body)
    
    print("=" * 80)


def send_email_with_preview(subject_email: str, recipient_email: str, subject: str, body: str):
    """
    Send email or show preview based on PREVIEW_MODE setting
    """
    if PREVIEW_MODE:
        preview_email(subject, recipient_email, subject_email, body)
        return {"status": "preview", "message": "Email preview displayed"}
    else:
        return gmail_send_email(subject_email, recipient_email, subject, body)


def is_quarter_start_reminder_day() -> tuple[bool, str]:
    """
    Check if today is the 7th of a quarter month (Jan, Apr, Jul, Oct)
    Returns: (is_reminder_day, quarter_info)
    """
    today = date.today()
    quarter_months = [1, 4, 7, 10]  # January, April, July, October
    
    # Always calculate current quarter info
    if today.month <= 3:
        quarter = "Q1"
    elif today.month <= 6:
        quarter = "Q2"
    elif today.month <= 9:
        quarter = "Q3"
    else:
        quarter = "Q4"
    
    year_short = str(today.year)[2:]
    quarter_info = f"{quarter}'{year_short}"
    
    # Check if today is the 7th of a quarter month
    is_reminder_day = today.month in quarter_months and today.day == 7
    
    return is_reminder_day, quarter_info


def get_active_funds() -> List[Dict[str, Any]]:
    """Get all active funds from the database"""
    try:
        db = next(get_db())
        try:
            funds = db.query(FundDetails).filter(FundDetails.scheme_status == "Active").all()
            return [
                {
                    "fund_id": fund.fund_id,
                    "scheme_name": fund.scheme_name,
                    "fund_manager": fund.investment_officer_name or "N/A"
                }
                for fund in funds
            ]
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error fetching active funds: {str(e)}")
        return []


def capital_call_reminder():
    """
    Check if it's the 7th of a quarter and send reminder to Fund Manager
    """
    logger.info("Checking for capital call reminders...")
    
    try:
        is_reminder_day, quarter_info = is_quarter_start_reminder_day()
        
        if not is_reminder_day:
            logger.info(f"Today ({date.today()}) is not a quarter reminder day (7th of Jan/Apr/Jul/Oct)")
            return
        
        logger.info(f"Today is capital call reminder day for {quarter_info}")
        
        # Get active funds
        active_funds = get_active_funds()
        
        if not active_funds:
            logger.warning("No active funds found")
            return
        
        # Prepare fund information for email
        fund_list = "\n".join([
            f"• {fund['scheme_name']} (ID: {fund['fund_id']}, Manager: {fund['fund_manager']})"
            for fund in active_funds
        ])
        
        # Compose stylized email
        subject = f"📈 Capital Call Reminder - {quarter_info} Quarterly Drawdowns"
        
        # Create HTML fund list
        fund_list_html = ""
        for i, fund in enumerate(active_funds, 1):
            fund_list_html += f"""
            <tr style="border-bottom: 1px solid #e2e8f0; background: #ffffff;">
                <td style="padding: 12px; text-align: center; font-weight: bold; color: #059669;">{i}</td>
                <td style="padding: 12px; font-weight: bold; color: #333;">{fund['scheme_name']}</td>
                <td style="padding: 12px; text-align: center; color: #666;">ID: {fund['fund_id']}</td>
                <td style="padding: 12px; color: #666;">{fund['fund_manager']}</td>
            </tr>"""
        
        html_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }}
                .header {{ background: linear-gradient(135deg, #059669 0%, #10b981 100%); color: white; padding: 30px; text-align: center; }}
                .content {{ padding: 30px; background: #fafafa; }}
                .fund-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; box-shadow: 0 2px 12px rgba(0,0,0,0.06); border-radius: 6px; overflow: hidden; }}
                .fund-table th {{ background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%); padding: 15px; text-align: left; font-weight: bold; color: #334155; border-bottom: 2px solid #059669; }}
                .alert-box {{ background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); border: 1px solid #f59e0b; border-radius: 10px; padding: 20px; margin: 20px 0; box-shadow: 0 2px 8px rgba(245, 158, 11, 0.1); }}
                .cta-button {{ display: inline-block; background: linear-gradient(135deg, #059669 0%, #10b981 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 20px 0; box-shadow: 0 3px 12px rgba(5, 150, 105, 0.3); transition: transform 0.2s ease; }}
                .cta-button:hover {{ transform: translateY(-1px); }}
                .footer {{ background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); padding: 20px; text-align: center; color: #64748b; font-size: 12px; }}
                .quarter-badge {{ background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%); color: #059669; padding: 8px 16px; border-radius: 20px; font-weight: bold; display: inline-block; box-shadow: 0 2px 6px rgba(5, 150, 105, 0.1); }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="margin: 0; font-size: 28px;">📈 Capital Call Reminder</h1>
                    <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">Time to Initiate Quarterly Drawdowns</p>
                </div>
                
                <div class="content">
                    <h2 style="color: #059669;">Hello Fund Manager! 👋</h2>
                    
                    <div class="alert-box">
                        <strong>🗓️ Quarterly Reminder:</strong> It's time to initiate drawdowns for 
                        <span class="quarter-badge">{quarter_info}</span>
                    </div>
                    
                    <h3 style="color: #333; margin-top: 30px;">💼 Active Funds Requiring Attention:</h3>
                    
                    <table class="fund-table">
                        <thead>
                            <tr>
                                <th style="width: 50px;">#</th>
                                <th>Fund Name</th>
                                <th style="width: 100px;">Fund ID</th>
                                <th style="width: 150px;">Manager</th>
                            </tr>
                        </thead>
                        <tbody>
                            {fund_list_html}
                        </tbody>
                    </table>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="https://compliance-system.netlify.app/dashboard" class="cta-button">
                            🚀 Access Dashboard & Initiate Drawdowns
                        </a>
                    </div>
                    
                    <div style="background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%); border-radius: 10px; padding: 20px; margin: 20px 0; border-left: 4px solid #059669;">
                        <h4 style="color: #059669; margin: 0 0 10px 0;">📋 Key Actions Required:</h4>
                        <ul style="margin: 0; padding-left: 20px; color: #065f46;">
                            <li>📊 Review fund performance and requirements for {quarter_info}</li>
                            <li>🎯 Determine drawdown percentage for each fund</li>
                            <li>📅 Determine drawdown due and notice date for each fund</li>
                            <li>📤 Generate capital call notices for LPs</li>
                            <li>✅ Preview and send notices to investors</li>
                        </ul>
                    </div>
                    
                    <div style="background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%); border-radius: 10px; padding: 15px; margin: 20px 0; border-left: 4px solid #059669;">
                        <p style="margin: 0; color: #059669; font-weight: bold;">💡 Pro Tip:</p>
                        <p style="margin: 5px 0 0 0; color: #065f46;">Access the Drawdowns section in your dashboard to quickly generate notices for all LPs in a fund with just a few clicks!</p>
                    </div>
                </div>
                
                <div class="footer">
                    <p><strong>AJVC Compliance Automation System</strong></p>
                    <p>This automated reminder is sent on the 7th of each quarter (Jan, Apr, Jul, Oct).</p>
                    <p>Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')} UTC </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Send email
        try:
            send_email_with_preview(
                subject_email="tech@ajuniorvc.com",
                recipient_email="aviral@ajuniorvc.com",
                subject=subject,
                body=html_body
            )
            logger.info(f"Capital call reminder sent successfully for {quarter_info}")
            
        except Exception as email_error:
            logger.error(f"Failed to send capital call reminder email: {str(email_error)}")
            
    except Exception as e:
        logger.error(f"Error in capital_call_reminder: {str(e)}")


def get_tasks_due_in_days(days: int) -> List[Dict[str, Any]]:
    """Get tasks that are due in specified number of days"""
    try:
        target_date = date.today() + timedelta(days=days)
        logger.info(f"Target date: {target_date}")
        
        db = next(get_db())
        try:
            # Query tasks with due date matching target date and in pending states
            tasks = db.query(ComplianceTask).filter(
                cast(ComplianceTask.deadline, Date) == target_date,
                ComplianceTask.state.in_(["Pending", "Review Required", "Open"])
            ).all()
            logger.info(f"Tasks: {tasks}")

            
            result = []
            for task in tasks:
                # Get assignee details
                assignee = None
                assignee_email = None
                if task.assignee_id:
                    assignee = db.query(User).filter(User.user_id == task.assignee_id).first()
                    if assignee:
                        assignee_email = assignee.email
                
                result.append({
                    "compliance_task_id": task.compliance_task_id,
                    "description": task.description,
                    "deadline": task.deadline.strftime('%Y-%m-%d'),
                    "state": task.state,
                    "category": task.category,
                    "assignee_id": task.assignee_id,
                    "assignee_name": assignee.name if assignee else "Unknown",
                    "assignee_email": assignee_email
                })
            
            return result
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error fetching tasks due in {days} days: {str(e)}")
        return []


def task_due_date_reminder():
    """
    Check for tasks due in 3 days and send stylized reminders to assignees and fund manager
    """
    logger.info("Checking for task due date reminders...")
    
    try:
        # Get tasks due in 3 days
        upcoming_tasks = get_tasks_due_in_days(3)
        logger.info(f"Upcoming tasks: {upcoming_tasks}")
        if not upcoming_tasks:
            logger.info("No tasks due in 3 days")
            return
        
        logger.info(f"Found {len(upcoming_tasks)} tasks due in 3 days")
        
        # Group tasks by assignee email
        tasks_by_assignee = {}
        for task in upcoming_tasks:
            assignee_email = task['assignee_email']
            assignee_name = task['assignee_name']
            
            if not assignee_email:
                # Unassigned tasks
                key = "unassigned"
            else:
                key = assignee_email
            
            if key not in tasks_by_assignee:
                tasks_by_assignee[key] = {
                    'name': assignee_name if assignee_email else 'Unassigned',
                    'email': assignee_email,
                    'tasks': []
                }
            tasks_by_assignee[key]['tasks'].append(task)
        
        # Send reminders to each assignee and always CC fund manager
        for assignee_key, assignee_data in tasks_by_assignee.items():
            tasks = assignee_data['tasks']
            assignee_name = assignee_data['name']
            assignee_email = assignee_data['email']
            
            # Determine recipient
            if assignee_email:
                primary_recipient = assignee_email
            else:
                # Unassigned tasks go directly to fund manager
                primary_recipient = "aviral@ajuniorvc.com"
                assignee_name = "Fund Manager (Unassigned Tasks)"
            
            # Prepare stylized task list for email
            task_list_html = ""
            for i, task in enumerate(tasks, 1):
                # State emoji mapping
                state_icons = {
                    "OPEN": "🆕", "Pending": "⏳",
                    "Review Required": "👀", "COMPLETED": "✅", "CANCELLED": "❌"
                }
                state_icon = state_icons.get(task['state'], "📋")
                
                # Category emoji mapping
                category_icons = {
                    "Compliance": "⚖️", "Documentation": "📄", "Review": "🔍",
                    "Audit": "🔍", "Reporting": "📊", "Legal": "⚖️"
                }
                category_icon = category_icons.get(task['category'], "📋")
                
                task_list_html += f"""
                <tr style="border-bottom: 1px solid #e2e8f0; background: #ffffff;">
                    <td style="padding: 12px; text-align: center; font-weight: bold; color: #059669;">{i}</td>
                    <td style="padding: 12px;">
                        <div style="font-weight: bold; color: #333; margin-bottom: 4px;">
                            {state_icon} {task['description'][:60]}{'...' if len(task['description']) > 60 else ''}
                        </div>
                        <div style="font-size: 12px; color: #666;">
                            {category_icon} <strong>Category:</strong> {task['category']} | 
                            <strong>State:</strong> {task['state']}
                        </div>
                    </td>
                    <td style="padding: 12px; text-align: center; font-weight: bold; color: #dc2626;">
                        📅 {task['deadline']}
                    </td>
                </tr>"""
            
            # Compose stylized email
            due_date = (date.today() + timedelta(days=3)).strftime('%B %d, %Y')
            subject = f"⏰ Task Reminder - {len(tasks)} task{'s' if len(tasks) > 1 else ''} due on {due_date}"
            
            # HTML email body with modern styling
            html_body = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }}
                    .header {{ background: linear-gradient(135deg, #047857 0%, #059669 100%); color: white; padding: 30px; text-align: center; }}
                    .content {{ padding: 30px; background: #fafafa; }}
                    .task-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; box-shadow: 0 2px 12px rgba(0,0,0,0.06); border-radius: 6px; overflow: hidden; }}
                    .task-table th {{ background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%); padding: 15px; text-align: left; font-weight: bold; color: #334155; border-bottom: 2px solid #047857; }}
                    .summary-box {{ background: linear-gradient(135deg, #fef7ed 0%, #fed7aa 100%); border: 1px solid #ea580c; border-radius: 10px; padding: 20px; margin: 20px 0; box-shadow: 0 2px 8px rgba(234, 88, 12, 0.1); }}
                    .cta-button {{ display: inline-block; background: linear-gradient(135deg, #047857 0%, #059669 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 20px 0; box-shadow: 0 3px 12px rgba(4, 120, 87, 0.3); transition: transform 0.2s ease; }}
                    .cta-button:hover {{ transform: translateY(-1px); }}
                    .footer {{ background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); padding: 20px; text-align: center; color: #64748b; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1 style="margin: 0; font-size: 28px;">⏰ Task Reminder</h1>
                        <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">Upcoming Compliance Tasks</p>
                    </div>
                    
                    <div class="content">
                        <h2 style="color: #047857;">Hello {assignee_name}! 👋</h2>
                        
                        <div class="summary-box">
                            <strong>📋 Summary:</strong> You have <strong>{len(tasks)} compliance task{'s' if len(tasks) > 1 else ''}</strong> 
                            due in <strong>3 days</strong> ({due_date}).
                        </div>
                        
                        <h3 style="color: #333; margin-top: 30px;">📝 Tasks Requiring Your Attention:</h3>
                        
                        <table class="task-table">
                            <thead>
                                <tr>
                                    <th style="width: 50px;">#</th>
                                    <th>Task Details</th>
                                    <th style="width: 120px;">Due Date</th>
                                </tr>
                            </thead>
                            <tbody>
                                {task_list_html}
                            </tbody>
                        </table>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="https://compliance-system.netlify.app/dashboard/task" class="cta-button">
                                🚀 Access Task Dashboard
                            </a>
                        </div>
                        
                        <div style="background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%); border-radius: 10px; padding: 20px; margin: 20px 0; border-left: 4px solid #059669;">
                            <h4 style="color: #059669; margin: 0 0 10px 0;">📋 Next Steps:</h4>
                            <ul style="margin: 0; padding-left: 20px; color: #065f46;">
                                <li>🔍 Review task details and requirements</li>
                                <li>📈 Update task status as you progress</li>
                                <li>✅ Complete tasks before the due date</li>
                                <li>💬 Add comments if you need assistance</li>
                            </ul>
                        </div>
                    </div>
                    
                    <div class="footer">
                        <p><strong>AJVC Compliance Automation System</strong></p>
                        <p>This is an automated reminder sent 3 days before task due dates.</p>
                        <p>Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')} UTC</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Send email to assignee
            try:
                send_email_with_preview(
                    subject_email="tech@ajuniorvc.com",
                    recipient_email=primary_recipient,
                    subject=subject,
                    body=html_body
                )
                logger.info(f"Task reminder sent to {primary_recipient} for {len(tasks)} tasks")
                
                # Also send to fund manager if different from primary recipient
                if primary_recipient != "aviral@ajuniorvc.com":
                    # Adjust subject for fund manager copy
                    fm_subject = f"📋 Task Reminder Copy - {assignee_name} has {len(tasks)} task{'s' if len(tasks) > 1 else ''} due"
                    fm_html_body = html_body.replace(
                        f"Hello {assignee_name}! 👋",
                        f"Hello Fund Manager! 👋<br><small style='color: #666;'>This is a copy of the reminder sent to {assignee_name}</small>"
                    )
                    
                    send_email_with_preview(
                        subject_email="tech@ajuniorvc.com",
                        recipient_email="aviral@ajuniorvc.com",
                        subject=fm_subject,
                        body=fm_html_body
                    )
                    logger.info(f"Task reminder copy sent to fund manager for {assignee_name}")
                
            except Exception as email_error:
                logger.error(f"Failed to send task reminder email to {primary_recipient}: {str(email_error)}")
                
    except Exception as e:
        logger.error(f"Error in task_due_date_reminder: {str(e)}")


def run_daily_reminders():
    """
    Main function to run all daily reminder checks
    """
    logger.info("=" * 60)
    logger.info("Starting Daily Reminder Service")
    logger.info(f"Current date: {date.today()}")
    logger.info(f"Current time: {datetime.now().strftime('%H:%M:%S')}")
    logger.info("=" * 60)
    
    try:
        # Run capital call reminder check
        capital_call_reminder()
        
        # Run task due date reminder check
        task_due_date_reminder()
        
        logger.info("Daily reminder service completed successfully")
        
    except Exception as e:
        logger.error(f"Error in daily reminder service: {str(e)}")
        raise
    
    logger.info("=" * 60)


def test_email_previews():
    """
    Test function to force generate email previews for testing
    """
    print("🧪 Testing Email Previews")
    print("=" * 50)
    
    # Force today to be a quarter reminder day for testing
    import datetime
    original_date = datetime.date
    
    class MockDate(datetime.date):
        @classmethod
        def today(cls):
            return cls(2025, 1, 7)  # Jan 7th, 2025 (Q1 reminder day)
    
    datetime.date = MockDate
    
    try:
        # Test capital call reminder
        print("\n📈 Testing Capital Call Reminder:")
        capital_call_reminder()
        
        # Test task reminder (with mock data)
        print("\n⏰ Testing Task Reminder:")
        task_due_date_reminder()
        
    finally:
        datetime.date = original_date
    
    print("\n✅ Preview test completed!")
    print("\nTo run normal service:")
    print("  python reminder_service.py")
    print("\nTo disable preview mode:")
    print("  Change PREVIEW_MODE = False at top of file")


if __name__ == "__main__":
    import sys
    
    # Check if we want to run preview test
    if len(sys.argv) > 1 and sys.argv[1] == "preview":
        test_email_previews()
        sys.exit(0)
    
    try:
        run_daily_reminders()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Daily reminder service failed: {str(e)}")
        sys.exit(1)