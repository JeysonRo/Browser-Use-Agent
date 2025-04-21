from playwright.sync_api import sync_playwright
import re
import time
from langchain_core.messages import AIMessage

def parse_steps(steps_text):
    """Parse the numbered steps from the planning agent output."""
    # Split by newlines and filter out empty lines
    lines = [line.strip() for line in steps_text.split('\n') if line.strip()]
    # Extract steps that start with numbers
    step_pattern = re.compile(r'^\d+\.\s*(.*)')
    steps = []
    
    for line in lines:
        match = step_pattern.match(line)
        if match:
            steps.append(match.group(1))
    
    # If no numbered steps were found, try to use the raw text
    if not steps and lines:
        steps = lines
        
    return steps

def browser_agent(state):
    # Instructions given to model
    """
    Execute the steps from the planning agent in a browser.
    
    Args:
        state (dict): The current state containing messages and steps
        
    Returns:
        dict: Updated state with execution results
    """
    steps_text = state["steps"]
    steps = parse_steps(steps_text)
    
    # Extract credentials if they exist
    credentials = state.get("credentials", None)
    secure_username = credentials.get("username", "demo_username") if credentials else "demo_username"
    secure_password = credentials.get("password", "demo_password") if credentials else "demo_password"
    
    # Mask password in logs
    display_password = "********" if credentials and credentials.get("password") else "demo_password"
    
    execution_log = []
    execution_log.append(f"Received {len(steps)} steps to execute:")
    for i, step in enumerate(steps):
        execution_log.append(f"{i+1}. {step}")
    
    if credentials:
        execution_log.append("\nUsing provided secure credentials (password masked)")
    else:
        execution_log.append("\nUsing demo credentials (username='demo_username', password='demo_password')")
        
    execution_log.append("\nStarting browser automation...")
    
    # Update logs before we start browser automation
    update_logs(state, execution_log)
    
    with sync_playwright() as p:
        try:
            # Simple launch of a browser - works locally without Docker
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(viewport={"width": 1600, "height": 900})  # Larger viewport for better visibility
            page = context.new_page()
            
            # Set a shorter default timeout for quicker feedback on errors
            page.set_default_timeout(15000)  # 15 seconds instead of default 30
            
            for i, step in enumerate(steps):
                try:
                    execution_log.append(f"\nExecuting step {i+1}: {step}")
                    # Update logs for each step start
                    update_logs(state, execution_log)
                    
                    # Special case for Canvas
                    if "canvas" in step.lower():
                        execution_log.append(f"  🌐 Detected Canvas reference. Navigating to Canvas LMS.")
                        page.goto("https://login.microsoftonline.com/8d84067d-9ad7-4572-9b10-133d36462aaa/saml2?SAMLRequest=jVJLT%2BMwEL7vr4h8d94kxGorFSpEJWArWjhwQYMzpZYcO3gcFv49bgqCPYC4%2BDCe76mZEHS6F%2FPB78w1Pg1IPnrptCExfkzZ4IywQIqEgQ5JeCnW88sLkcep6J31VlrNvkB%2BRgAROq%2BsYdFyMWX30Mgqk3XBmzI8JUDFAaucN1VWABZlk8uaRbfoKGCmLFAEINGAS0MejA%2BjND%2FiacnzbJNmIi1F3tyxaBFyKAN%2BRO2870kkibaPysSdks6S3XprtDIYS9slx%2B1xmVZ1yxtoa14e1cHBQ5byrCjaoiqrHACSfbqcRfOPCKfW0NChW6N7VhJvri8%2BpbbaOtVCb%2FWrR7kzSsYqOHaD9IM7aI5uRlIWrd6LPFGmVebx5w4fDkskzjebFV%2F9XW%2FYbLLnEWMzbrY38TsPY6RJ8hU8ORzEVZBdLlZWK%2FkanVnXgf%2FeVRZn40S1fDuuisFQj1JtFbahMa3tv1OH4HHKgj6yZHYQ%2Ff%2FwZn%2FeAA%3D%3D&SigAlg=http%3A%2F%2Fwww.w3.org%2F2001%2F04%2Fxmldsig-more%23rsa-sha256&Signature=nkAcO4Lggvjim35rvTw%2Fq98Cuo58gTMU%2FKo8fvUqbbpEAhvVDpbsFqiwN5f15FvoSsIAWVXNg5LUQKTSQ7S6cXwwzyosQtAUtO9vlfjUIzsLgkCv%2BiQkG5ZaVpmlk2KwXCJNTq1XAnWDyjuOBqsHzSs61gfjg%2BbgnBvdNCZLoNt4CThVnah09OvEzf4OMFDrjzo5mqyjIQv1zZn21qmaf%2F8h7WTXy1ze4SjkP7lbAHrhNGn0V0OUVvWDWP2UxJJ%2F1Ip86btqiedNtKOtX%2FLev1HgWnoHgQykFPhiblKwFAYbTT0NVsVQmTx%2BVTEL02DG9%2F5tksekseFikah4Hwi%2BqA%3D%3D", wait_until="domcontentloaded")
                        time.sleep(1)  # Reduced from 2 seconds to 1
                        execution_log.append("  ✅ Canvas login page loaded")
                        continue
                    
                    # Navigate to URL
                    if "go to" in step.lower() or "navigate to" in step.lower() or "open" in step.lower():
                        url_match = re.search(r'https?://[^\s]+', step)
                        if url_match:
                            url = url_match.group(0)
                        else:
                            # Extract domain from text
                            domain_match = re.search(r'(?:go to|navigate to|open)\s+(?:the\s+)?(?:website\s+)?([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', step, re.IGNORECASE)
                            if domain_match:
                                url = f"https://{domain_match.group(1)}"
                            else:
                                # Check for specific websites
                                if "google" in step.lower():
                                    url = "https://www.google.com"
                                elif "youtube" in step.lower():
                                    url = "https://www.youtube.com"
                                elif "facebook" in step.lower():
                                    url = "https://www.facebook.com"
                                elif "twitter" in step.lower() or "x" in step.lower():
                                    url = "https://twitter.com"
                                elif "canvas" in step.lower():
                                    url = "https://login.microsoftonline.com/8d84067d-9ad7-4572-9b10-133d36462aaa/saml2?SAMLRequest=jVJLT%2BMwEL7vr4h8d94kxGorFSpEJWArWjhwQYMzpZYcO3gcFv49bgqCPYC4%2BDCe76mZEHS6F%2FPB78w1Pg1IPnrptCExfkzZ4IywQIqEgQ5JeCnW88sLkcep6J31VlrNvkB%2BRgAROq%2BsYdFyMWX30Mgqk3XBmzI8JUDFAaucN1VWABZlk8uaRbfoKGCmLFAEINGAS0MejA%2BjND%2FiacnzbJNmIi1F3tyxaBFyKAN%2BRO2870kkibaPysSdks6S3XprtDIYS9slx%2B1xmVZ1yxtoa14e1cHBQ5byrCjaoiqrHACSfbqcRfOPCKfW0NChW6N7VhJvri8%2BpbbaOtVCb%2FWrR7kzSsYqOHaD9IM7aI5uRlIWrd6LPFGmVebx5w4fDkskzjebFV%2F9XW%2FYbLLnEWMzbrY38TsPY6RJ8hU8ORzEVZBdLlZWK%2FkanVnXgf%2FeVRZn40S1fDuuisFQj1JtFbahMa3tv1OH4HHKgj6yZHYQ%2Ff%2FwZn%2FeAA%3D%3D&SigAlg=http%3A%2F%2Fwww.w3.org%2F2001%2F04%2Fxmldsig-more%23rsa-sha256&Signature=nkAcO4Lggvjim35rvTw%2Fq98Cuo58gTMU%2FKo8fvUqbbpEAhvVDpbsFqiwN5f15FvoSsIAWVXNg5LUQKTSQ7S6cXwwzyosQtAUtO9vlfjUIzsLgkCv%2BiQkG5ZaVpmlk2KwXCJNTq1XAnWDyjuOBqsHzSs61gfjg%2BbgnBvdNCZLoNt4CThVnah09OvEzf4OMFDrjzo5mqyjIQv1zZn21qmaf%2F8h7WTXy1ze4SjkP7lbAHrhNGn0V0OUVvWDWP2UxJJ%2F1Ip86btqiedNtKOtX%2FLev1HgWnoHgQykFPhiblKwFAYbTT0NVsVQmTx%2BVTEL02DG9%2F5tksekseFikah4Hwi%2BqA%3D%3D"
                                else:
                                    execution_log.append("  ❌ Could not extract URL from step")
                                    continue
                        
                        execution_log.append(f"  🌐 Navigating to {url}")
                        page.goto(url, wait_until="domcontentloaded")
                        time.sleep(1)  # Reduced from 2 seconds to 1
                    
                    # Click on element
                    elif "click" in step.lower():
                        # Try to find element by text
                        text_match = re.search(r'click (?:on )?(?:the )?["\']?([^"\']+)["\']?', step, re.IGNORECASE)
                        if text_match:
                            text = text_match.group(1)
                            execution_log.append(f"  🖱️ Clicking on element containing text: {text}")
                            
                            # Keep trying for a few seconds (pages might be loading)
                            max_attempts = 3  # Reduced from 5 to 3 attempts
                            for attempt in range(max_attempts):
                                try:
                                    # Try exact text
                                    page.click(f"text='{text}'")
                                    execution_log.append(f"  ✅ Successfully clicked on '{text}'")
                                    break
                                except:
                                    try:
                                        # Try contains text
                                        page.click(f"text={text}")
                                        execution_log.append(f"  ✅ Successfully clicked on text containing '{text}'")
                                        break
                                    except:
                                        try:
                                            # Try button with text
                                            page.click(f"button:has-text('{text}')")
                                            execution_log.append(f"  ✅ Successfully clicked on button with '{text}'")
                                            break
                                        except:
                                            try:
                                                # Try link with text
                                                page.click(f"a:has-text('{text}')")
                                                execution_log.append(f"  ✅ Successfully clicked on link with '{text}'")
                                                break
                                            except Exception as e:
                                                if attempt == max_attempts - 1:
                                                    execution_log.append(f"  ❌ Failed to click after {max_attempts} attempts: {str(e)}")
                                                else:
                                                    # Wait and try again (shorter wait)
                                                    time.sleep(0.5)  # Reduced from 1 second to 0.5
                        else:
                            execution_log.append("  ❌ Could not determine what to click on")
                    
                    # Type text
                    elif any(keyword in step.lower() for keyword in ["type", "enter", "input", "fill"]):
                        # Try to extract field and text
                        field_text_match = re.search(r'(?:type|enter|input|fill)\s+["\']?([^"\']+)["\']?\s+(?:in|into|to)?\s+(?:the )?([^"\']+)', step, re.IGNORECASE)
                        if not field_text_match:
                            field_text_match = re.search(r'(?:in|into|to)\s+(?:the )?([^"\']+)\s+(?:type|enter|input|fill)\s+["\']?([^"\']+)["\']?', step, re.IGNORECASE)
                        
                        # Special case for logins - identify when we need to enter credentials
                        if "username" in step.lower() or "email" in step.lower() or "login" in step.lower() or "userid" in step.lower():
                            execution_log.append(f"  ⌨️ Attempting to enter username: {secure_username}")
                            update_logs(state, execution_log)
                            
                            # Try various username field selectors
                            username_entered = False
                            try:
                                # Canvas specific
                                page.fill("#pseudonym_session_unique_id", secure_username)
                                username_entered = True
                                execution_log.append(f"  ✅ Username entered with Canvas-specific selector")
                                update_logs(state, execution_log)
                            except:
                                try:
                                    # Microsoft login specific
                                    page.fill("input[type='email']", secure_username)
                                    username_entered = True
                                    execution_log.append(f"  ✅ Username entered with Microsoft-specific selector")
                                    update_logs(state, execution_log)
                                    
                                    # Microsoft login requires clicking Next after entering username
                                    execution_log.append(f"  🖱️ Attempting to click Next button for Microsoft login")
                                    update_logs(state, execution_log)
                                    
                                    # Try different selectors for the Next button
                                    next_button_clicked = False
                                    try:
                                        page.click("input[type='submit']")
                                        execution_log.append("  ✅ Clicked Next button (submit input)")
                                        update_logs(state, execution_log)
                                        next_button_clicked = True
                                    except Exception as e:
                                        execution_log.append(f"  ℹ️ Could not click submit input: {str(e)}")
                                        update_logs(state, execution_log)

                                    if not next_button_clicked:
                                        try:
                                            page.click("#idSIButton9")
                                            execution_log.append("  ✅ Clicked Next button (idSIButton9)")
                                            update_logs(state, execution_log)
                                            next_button_clicked = True
                                        except Exception as e:
                                            execution_log.append(f"  ℹ️ Could not click idSIButton9: {str(e)}")
                                            update_logs(state, execution_log)

                                    if not next_button_clicked:
                                        try:
                                            page.click("text=Next")
                                            execution_log.append("  ✅ Clicked Next button (text)")
                                            update_logs(state, execution_log)
                                            next_button_clicked = True
                                        except Exception as e:
                                            execution_log.append(f"  ℹ️ Could not click 'Next' text: {str(e)}")
                                            update_logs(state, execution_log)

                                    if not next_button_clicked:
                                        try:
                                            page.keyboard.press("Enter")
                                            execution_log.append("  ✅ Pressed Enter to proceed")
                                            update_logs(state, execution_log)
                                            next_button_clicked = True
                                        except Exception as e:
                                            execution_log.append(f"  ❌ Failed to click Next: {str(e)}")
                                            update_logs(state, execution_log)
                                    
                                    # Wait for password page to load
                                    execution_log.append("  ⏱️ Waiting for password page to load...")
                                    update_logs(state, execution_log)
                                    time.sleep(3)  # Increased from 2 to 3 seconds
                                    
                                    # Verify we're on the password page before proceeding
                                    try:
                                        if page.query_selector("input[type='password']") or page.query_selector("#passwordInput"):
                                            execution_log.append("  ✅ Successfully navigated to password page")
                                        else:
                                            execution_log.append("  ⚠️ Password input not found. May need to try again.")
                                        update_logs(state, execution_log)
                                    except Exception as e:
                                        execution_log.append(f"  ℹ️ Could not verify password page: {str(e)}")
                                        update_logs(state, execution_log)
                                except:
                                    try:
                                        # Generic username/email fields
                                        for selector in ["#username", "input[name='username']", "input[name='email']", 
                                                        "input[type='text']", "[placeholder*='user' i]", 
                                                        "[placeholder*='email' i]", "[id*='user' i]", "[id*='email' i]"]:
                                            try:
                                                page.fill(selector, secure_username)
                                                username_entered = True
                                                break
                                            except:
                                                continue
                                    except Exception as e:
                                        execution_log.append(f"  ℹ️ Could not find username field: {str(e)}")
                            
                            if username_entered:
                                execution_log.append(f"  ✅ Username entered successfully")
                                continue
                                
                        if "password" in step.lower() or "pass" in step.lower():
                            execution_log.append(f"  ⌨️ Attempting to enter password: {display_password}")
                            update_logs(state, execution_log)
                            
                            # Try various password field selectors
                            password_entered = False
                            try:
                                # Canvas specific
                                page.fill("#pseudonym_session_password", secure_password)
                                password_entered = True
                                execution_log.append(f"  ✅ Password entered with Canvas-specific selector")
                                update_logs(state, execution_log)
                            except:
                                try:
                                    # Microsoft login specific password field
                                    page.fill("input[type='password']", secure_password)
                                    password_entered = True
                                    execution_log.append(f"  ✅ Password entered with Microsoft-specific selector")
                                    update_logs(state, execution_log)
                                    
                                    # Microsoft login requires clicking Sign in after entering password
                                    execution_log.append(f"  🖱️ Attempting to click Sign in button for Microsoft login")
                                    update_logs(state, execution_log)
                                    
                                    # Try different selectors for the Sign in button
                                    sign_in_clicked = False
                                    try:
                                        page.click("input[type='submit']")
                                        execution_log.append("  ✅ Clicked Sign in button (submit input)")
                                        update_logs(state, execution_log)
                                        sign_in_clicked = True
                                    except Exception as e:
                                        execution_log.append(f"  ℹ️ Could not click submit input: {str(e)}")
                                        update_logs(state, execution_log)
                                    
                                    if not sign_in_clicked:
                                        try:
                                            page.click("#idSIButton9")
                                            execution_log.append("  ✅ Clicked Sign in button (idSIButton9)")
                                            update_logs(state, execution_log)
                                            sign_in_clicked = True
                                        except Exception as e:
                                            execution_log.append(f"  ℹ️ Could not click idSIButton9: {str(e)}")
                                            update_logs(state, execution_log)
                                    
                                    if not sign_in_clicked:
                                        try:
                                            page.click("text=Sign in")
                                            execution_log.append("  ✅ Clicked Sign in button (text)")
                                            update_logs(state, execution_log)
                                            sign_in_clicked = True
                                        except Exception as e:
                                            execution_log.append(f"  ℹ️ Could not click 'Sign in' text: {str(e)}")
                                            update_logs(state, execution_log)
                                    
                                    if not sign_in_clicked:
                                        try:
                                            page.keyboard.press("Enter")
                                            execution_log.append("  ✅ Pressed Enter to sign in")
                                            update_logs(state, execution_log)
                                            sign_in_clicked = True
                                        except Exception as e:
                                            execution_log.append(f"  ❌ Failed to click Sign in: {str(e)}")
                                            update_logs(state, execution_log)
                                    
                                    # Wait for sign-in to complete
                                    execution_log.append("  ⏱️ Waiting for sign-in to complete...")
                                    update_logs(state, execution_log)
                                    time.sleep(4)  # Increased from 2 to 4 seconds
                                    
                                    # Handle 2FA (Two-Factor Authentication)
                                    execution_log.append(f"  🔍 Checking for 2FA/verification screens...")
                                    
                                    # Check for common 2FA indicators
                                    two_fa_detected = False
                                    try:
                                        # Look for common 2FA text indicators
                                        two_fa_texts = [
                                            "two-factor", "2-factor", "two factor", "2 factor", 
                                            "verification", "verify your identity", "additional security",
                                            "approve sign-in", "approve sign in", "authentication",
                                            "security code", "verification code", "one-time code",
                                            "enter code", "choose a method", "authenticator app"
                                        ]
                                        
                                        for text in two_fa_texts:
                                            if page.query_selector(f"text={text}"):
                                                two_fa_detected = True
                                                execution_log.append(f"  ⚠️ Two-factor authentication detected: '{text}'")
                                                break
                                    except Exception:
                                        pass
                                    
                                    if two_fa_detected:
                                        execution_log.append(f"  ⚠️ TWO-FACTOR AUTHENTICATION REQUIRED")
                                        execution_log.append(f"  ⚠️ Since this requires human interaction, the browser will be kept open for 60 seconds.")
                                        execution_log.append(f"  ⚠️ Please complete the 2FA verification manually within this time.")
                                        
                                        # Long wait to allow for manual 2FA completion
                                        for i in range(12):  # 12 x 5 seconds = 60 seconds total
                                            try:
                                                # Update the execution result to show progress in real-time
                                                execution_log.append(f"  ⏱️ Waiting for manual 2FA verification... {(i+1)*5} seconds elapsed")
                                                update_logs(state, execution_log)
                                                
                                                time.sleep(5)
                                                # Check if we've moved past the 2FA page
                                                if page.query_selector("text=Dashboard") or page.query_selector("text=Courses") or page.query_selector("text=Calendar"):
                                                    execution_log.append(f"  ✅ 2FA verification appears to be complete!")
                                                    update_logs(state, execution_log)
                                                    break
                                            except Exception:
                                                pass
                                        
                                        execution_log.append(f"  ℹ️ Continuing with automation...")
                                    
                                    # Proactively handle "Stay signed in" dialog without waiting for a specific step
                                    execution_log.append(f"  🔍 Attempting to handle any 'Stay signed in' dialog...")
                                    
                                    # First try looking for the dialog
                                    stay_dialog_visible = False
                                    try:
                                        # Different possible texts on the dialog
                                        for text in ["Stay signed in", "Keep me signed in", "Stay signed in?", "Remember me"]:
                                            if page.query_selector(f"text={text}"):
                                                stay_dialog_visible = True
                                                execution_log.append(f"  ✅ Found dialog with text: '{text}'")
                                                break
                                    except Exception:
                                        pass
                                        
                                    # If dialog found, try clicking various buttons
                                    if stay_dialog_visible:
                                        # Try all possible button options with very short timeouts
                                        page.set_default_timeout(1000)  # 1 second timeout for speed
                                        
                                        # Try Yes button
                                        try:
                                            page.click("text=Yes")
                                            execution_log.append(f"  ✅ Clicked 'Yes' button")
                                            update_logs(state, execution_log)
                                            time.sleep(1)
                                            continue  # Continue with next steps instead of return
                                        except Exception:
                                            pass
                                                
                                        # Try No button
                                        try:
                                            page.click("text=No")
                                            execution_log.append(f"  ✅ Clicked 'No' button")
                                            update_logs(state, execution_log)
                                            time.sleep(1)
                                            continue  # Continue with next steps instead of return
                                        except Exception:
                                            pass
                                                
                                        # Try button with ID
                                        try:
                                            page.click("#idSIButton9")
                                            execution_log.append(f"  ✅ Clicked button with ID 'idSIButton9'")
                                            update_logs(state, execution_log)
                                            time.sleep(1)
                                            continue  # Continue with next steps instead of return
                                        except Exception:
                                            pass
                                                
                                        # Try any button
                                        try:
                                            page.click("button")
                                            execution_log.append(f"  ✅ Clicked first button found")
                                            update_logs(state, execution_log)
                                            time.sleep(1)
                                            continue  # Continue with next steps instead of return
                                        except Exception as e:
                                            execution_log.append(f"  ❌ Failed to interact with dialog: {str(e)}")
                                        
                                        # Reset timeout
                                        page.set_default_timeout(30000)  # Reset to 30 seconds
                                    else:
                                        execution_log.append(f"  ℹ️ No 'Stay signed in' dialog detected, continuing...")
                                except Exception as e:
                                    execution_log.append(f"  ❌ Microsoft login handling failed: {str(e)}")
                                    
                                # Continue with generic password fields if Microsoft login handling failed
                                if not password_entered:
                                    try:
                                        for selector in ["#password", "input[name='password']", "input[type='password']", 
                                                        "[placeholder*='password' i]", "[id*='pass' i]"]:
                                            try:
                                                page.fill(selector, secure_password)
                                                password_entered = True
                                                break
                                            except:
                                                continue
                                    except Exception as e:
                                        execution_log.append(f"  ℹ️ Could not find password field: {str(e)}")
                            
                            if password_entered:
                                execution_log.append(f"  ✅ Password entered successfully")
                                continue
                        
                        if field_text_match:
                            # Extract text and field based on match order
                            if "type" in step.lower() or "enter" in step.lower() or "input" in step.lower() or "fill" in step.lower():
                                text = field_text_match.group(1)
                                field = field_text_match.group(2)
                            else:
                                field = field_text_match.group(1)
                                text = field_text_match.group(2)
                                
                            execution_log.append(f"  ⌨️ Typing '{text}' into field: {field}")
                            
                            # Try multiple strategies with retries
                            max_attempts = 3  # Reduced from 5 to 3 attempts
                            for attempt in range(max_attempts):
                                try:
                                    # Try by placeholder
                                    page.fill(f"[placeholder*='{field}' i]", text)
                                    execution_log.append(f"  ✅ Text entered by placeholder")
                                    break
                                except:
                                    try:
                                        # Try by label
                                        page.fill(f"label:has-text('{field}') >> input", text)
                                        execution_log.append(f"  ✅ Text entered by label")
                                        break
                                    except:
                                        try:
                                            # Try by field name attribute
                                            page.fill(f"[name*='{field}' i]", text)
                                            execution_log.append(f"  ✅ Text entered by name attribute")
                                            break
                                        except:
                                            try:
                                                # Try by id containing the field name
                                                page.fill(f"[id*='{field}' i]", text)
                                                execution_log.append(f"  ✅ Text entered by id")
                                                break
                                            except Exception as e:
                                                if attempt == max_attempts - 1:
                                                    execution_log.append(f"  ❌ Failed to fill text after {max_attempts} attempts: {str(e)}")
                                                else:
                                                    # Wait and try again (shorter wait)
                                                    time.sleep(0.5)  # Reduced from 1 second to 0.5
                        else:
                            execution_log.append("  ❌ Could not determine what to type or where")
                    
                    # Wait explicitly
                    elif "wait" in step.lower():
                        seconds = 2  # Default wait time
                        time_match = re.search(r'wait\s+(?:for\s+)?(\d+)', step, re.IGNORECASE)
                        if time_match:
                            seconds = int(time_match.group(1))
                            seconds = min(seconds, 10)  # Cap at 10 seconds
                        
                        execution_log.append(f"  ⏱️ Waiting for {seconds} seconds")
                        time.sleep(seconds)
                    
                    # Submit form
                    elif "submit" in step.lower():
                        execution_log.append(f"  📝 Submitting form")
                        try:
                            # Try to find submit button
                            page.click("button[type='submit']")
                            execution_log.append(f"  ✅ Clicked submit button")
                        except:
                            try:
                                page.click("input[type='submit']")
                                execution_log.append(f"  ✅ Clicked submit input")
                            except:
                                try:
                                    page.click("text=Submit")
                                    execution_log.append(f"  ✅ Clicked element with 'Submit' text")
                                except:
                                    try:
                                        # Try to press Enter on the active element
                                        page.keyboard.press("Enter")
                                        execution_log.append(f"  ✅ Pressed Enter key")
                                    except Exception as e:
                                        execution_log.append(f"  ❌ Failed to submit form: {str(e)}")
                    
                    # Handle "Stay signed in" dialog that might appear after login
                    elif "stay" in step.lower() or "signed in" in step.lower() or "remember" in step.lower() or "verify" in step.lower():
                        execution_log.append(f"  🔍 Looking for 'Stay signed in' dialog")
                        try:
                            # Check for Microsoft's "Stay signed in?" dialog and click "Yes"
                            page.click("text=Yes")
                            execution_log.append(f"  ✅ Clicked 'Yes' on stay signed in dialog")
                        except:
                            try:
                                page.click("text=No")
                                execution_log.append(f"  ✅ Clicked 'No' on stay signed in dialog")
                            except:
                                try:
                                    # Try to find buttons with specific IDs
                                    page.click("#idSIButton9")
                                    execution_log.append(f"  ✅ Clicked confirmation button by ID")
                                except:
                                    try:
                                        # Try to find any button and click the first one
                                        page.click("button")
                                        execution_log.append(f"  ✅ Clicked first button on dialog")
                                    except Exception as e:
                                        execution_log.append(f"  ❌ Stay signed in dialog not found or couldn't be handled: {str(e)}")
                    
                    # Handle 2FA verification steps
                    elif any(keyword in step.lower() for keyword in ["two factor", "2fa", "verification", "verify", "authenticate", "code", "approval"]):
                        execution_log.append(f"  🔒 Two-factor authentication step detected")
                        execution_log.append(f"  ⚠️ TWO-FACTOR AUTHENTICATION REQUIRES YOUR ATTENTION")
                        execution_log.append(f"  ⚠️ Please check your phone/email/authenticator app and complete verification")
                        execution_log.append(f"  ⏱️ Waiting up to 60 seconds for you to complete 2FA verification...")
                        
                        # Look for common verification methods and provide helpful instructions
                        try:
                            if page.query_selector("text=phone"):
                                execution_log.append(f"  📱 Appears to be a phone verification method")
                            elif page.query_selector("text=email"):
                                execution_log.append(f"  📧 Appears to be an email verification method")
                            elif page.query_selector("text=app"):
                                execution_log.append(f"  📲 Appears to be an authenticator app verification method")
                            elif page.query_selector("text=code"):
                                execution_log.append(f"  🔢 Appears to require a verification code")
                        except Exception:
                            pass
                            
                        # Long wait to allow for manual 2FA completion
                        for i in range(12):  # 12 x 5 seconds = 60 seconds total
                            try:
                                # Update the execution result to show progress in real-time
                                execution_log.append(f"  ⏱️ Waiting for manual 2FA verification... {(i+1)*5} seconds elapsed")
                                update_logs(state, execution_log)
                                
                                time.sleep(5)
                                # Check if we've moved past the 2FA page
                                if page.query_selector("text=Dashboard") or page.query_selector("text=Courses") or page.query_selector("text=Calendar"):
                                    execution_log.append(f"  ✅ 2FA verification appears to be complete!")
                                    update_logs(state, execution_log)
                                    break
                            except Exception:
                                pass
                        
                        execution_log.append(f"  ✅ Continuing with next steps...")
                    
                    # Generic action if not matched above
                    else:
                        execution_log.append(f"  ❓ Step not recognized as a specific action, treating as text search")
                        # Try to find any element containing this text and click it
                        try:
                            page.click(f"text={step}")
                            execution_log.append(f"  ✅ Found and clicked on an element with this text")
                        except Exception as e:
                            execution_log.append(f"  ℹ️ Could not perform action automatically: {str(e)}")
                    
                    time.sleep(0.5)  # Brief pause between steps (reduced from 1s to 0.5s)
                    execution_log.append("  ✅ Step completed")
                    update_logs(state, execution_log)
                    
                except Exception as e:
                    execution_log.append(f"  ❌ Error executing step: {str(e)}")
                    update_logs(state, execution_log)
            
            # Take a screenshot at the end
            try:
                screenshot_path = "final_state.png"
                page.screenshot(path=screenshot_path)
                execution_log.append(f"\n📸 Final screenshot saved to {screenshot_path}")
            except Exception as e:
                execution_log.append(f"\n❌ Failed to take screenshot: {str(e)}")
            
            # Add a message asking user to close the browser
            execution_log.append("\n✨ Browser automation completed. The browser will remain open for 20 seconds so you can see the final state.")
            update_logs(state, execution_log)
            
            # Wait for user to view the final state
            time.sleep(20)  # Keep browser open for 20 seconds after completion (increased from 10 for better user experience)
            
            # Close browser
            browser.close()
            
        except Exception as e:
            execution_log.append(f"\n❌ Major error: {str(e)}")
            update_logs(state, execution_log)
    
    final_result = "\n".join(execution_log)
    
    # Make sure the final result is fully updated
    return {
        "messages": state["messages"] + [AIMessage(content=final_result)],
        "steps": final_result
    }

def update_logs(state, execution_log):
    """Helper function to update the logs in the state"""
    current_log = "\n".join(execution_log)
    state["steps"] = current_log
