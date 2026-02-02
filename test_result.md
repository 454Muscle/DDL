#====================================================================================================
# START - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================

# THIS SECTION CONTAINS CRITICAL TESTING INSTRUCTIONS FOR BOTH AGENTS
# BOTH MAIN_AGENT AND TESTING_AGENT MUST PRESERVE THIS ENTIRE BLOCK

# Communication Protocol:
# If the `testing_agent` is available, main agent should delegate all testing tasks to it.
#
# You have access to a file called `test_result.md`. This file contains the complete testing state
# and history, and is the primary means of communication between main and the testing agent.
#
# Main and testing agents must follow this exact format to maintain testing data. 
# The testing data must be entered in yaml format Below is the data structure:
# 
## user_problem_statement: {problem_statement}
## backend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.py"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## frontend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.js"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## metadata:
##   created_by: "main_agent"
##   version: "1.0"
##   test_sequence: 0
##   run_ui: false
##
## test_plan:
##   current_focus:
##     - "Task name 1"
##     - "Task name 2"
##   stuck_tasks:
##     - "Task name with persistent issues"
##   test_all: false
##   test_priority: "high_first"  # or "sequential" or "stuck_first"
##
## agent_communication:
##     -agent: "main"  # or "testing" or "user"
##     -message: "Communication message between agents"

# Protocol Guidelines for Main agent
#
# 1. Update Test Result File Before Testing:
#    - Main agent must always update the `test_result.md` file before calling the testing agent
#    - Add implementation details to the status_history
#    - Set `needs_retesting` to true for tasks that need testing
#    - Update the `test_plan` section to guide testing priorities
#    - Add a message to `agent_communication` explaining what you've done
#
# 2. Incorporate User Feedback:
#    - When a user provides feedback that something is or isn't working, add this information to the relevant task's status_history
#    - Update the working status based on user feedback
#    - If a user reports an issue with a task that was marked as working, increment the stuck_count
#    - Whenever user reports issue in the app, if we have testing agent and task_result.md file so find the appropriate task for that and append in status_history of that task to contain the user concern and problem as well 
#
# 3. Track Stuck Tasks:
#    - Monitor which tasks have high stuck_count values or where you are fixing same issue again and again, analyze that when you read task_result.md
#    - For persistent issues, use websearch tool to find solutions
#    - Pay special attention to tasks in the stuck_tasks list
#    - When you fix an issue with a stuck task, don't reset the stuck_count until the testing agent confirms it's working
#
# 4. Provide Context to Testing Agent:
#    - When calling the testing agent, provide clear instructions about:
#      - Which tasks need testing (reference the test_plan)
#      - Any authentication details or configuration needed
#      - Specific test scenarios to focus on
#      - Any known issues or edge cases to verify
#
# 5. Call the testing agent with specific instructions referring to test_result.md
#
# IMPORTANT: Main agent must ALWAYS update test_result.md BEFORE calling the testing agent, as it relies on this file to understand what to test next.

#====================================================================================================
# END - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================


#====================================================================================================
# Testing Data - Main Agent and testing sub agent both should log testing data below this section
#====================================================================================================

user_problem_statement: "Add a new 'Site' column to downloads and collect required site name + URL on submissions; additionally, add optional Google reCAPTCHA v2 configurable via Admin to replace math captcha on Submit and/or Auth."

backend:
  - task: "Site fields on submissions/downloads"
    implemented: true
    working: true
    file: "/app/backend/server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
      - working: true
        agent: "main"
        comment: "Added site_name + site_url to SubmissionCreate; persisted to submissions; approval copies fields into downloads. Manual curl verified approved download returns site fields."
      - working: true
        agent: "testing"
        comment: "✅ TESTED: Backend API returns site fields correctly. Downloads API shows site_name and site_url for items that have them. Integration working properly."
      - working: true
        agent: "testing"
        comment: "✅ COMPREHENSIVE BACKEND TESTING COMPLETE: All site field functionality verified. 1) /api/captcha generates math captcha correctly. 2) Submissions with site_name (≤15 chars) and site_url (http/https required) work perfectly with math captcha. 3) Approved submissions correctly copy site fields to downloads. 4) Site URL validation properly rejects URLs without http/https prefix. 5) Site name validation rejects names >15 characters. All 53 backend API tests passed (100% success rate)."

  - task: "Google reCAPTCHA v2 verification + settings"
    implemented: true
    working: true
    file: "/app/backend/server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
      - working: true
        agent: "main"
        comment: "Added SiteSettings recaptcha keys/toggles; /api/recaptcha/settings public endpoint; server-side verification via google siteverify when enabled; /api/settings hides secret key. Manual curl verified secret not exposed."
      - working: true
        agent: "testing"
        comment: "✅ TESTED: reCAPTCHA settings API working. Admin can update keys and toggles. Backend properly validates and saves settings. Frontend receives correct configuration."
      - working: true
        agent: "testing"
        comment: "✅ COMPREHENSIVE BACKEND TESTING COMPLETE: All reCAPTCHA functionality verified. 1) /api/recaptcha/settings returns only site_key + toggles (no secret exposed). 2) /api/settings never returns recaptcha_secret_key (properly null). 3) Admin settings validation: enabling reCAPTCHA without keys properly rejected (400), enabling with keys succeeds (200). 4) When reCAPTCHA enabled for submissions, requests without recaptcha_token properly rejected with 'Invalid reCAPTCHA'. 5) When reCAPTCHA enabled for auth, registration without recaptcha_token properly rejected. All security and validation requirements met."

frontend:
  - task: "Submit page: required site fields + reCAPTCHA widget toggle"
    implemented: true
    working: true
    file: "/app/frontend/src/pages/SubmitPage.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
      - working: true
        agent: "main"
        comment: "Added site name/url inputs (required) and reCAPTCHA widget when enabled via /api/recaptcha/settings; fallback to math captcha otherwise. Screenshot-based smoke test passed."
      - working: true
        agent: "testing"
        comment: "✅ TESTED: Site fields validation working correctly - site name max 15 chars, site URL must start with http/https. reCAPTCHA widget displays when enabled with dummy keys, math captcha shows when disabled. UI switching works properly."

  - task: "Home page: add Site column"
    implemented: true
    working: true
    file: "/app/frontend/src/pages/HomePage.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
      - working: true
        agent: "main"
        comment: "Added Site column to downloads table. Renders link with target=_blank when site_url present, otherwise shows '---'. Screenshot-based smoke test passed."
      - working: true
        agent: "testing"
        comment: "✅ TESTED: Site column working correctly. Table shows 'SITE' header (uppercase), displays clickable links for items with site_url, shows '---' for items without site. Backend API returns site data correctly. Minor: Header shows 'SITE' instead of 'Site' but functionality works."

  - task: "Admin dashboard: reCAPTCHA keys + toggles"
    implemented: true
    working: true
    file: "/app/frontend/src/pages/AdminDashboardPage.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
      - working: true
        agent: "main"
        comment: "Added Google reCAPTCHA 2.0 section with Site Key + Secret Key inputs and toggles for Submit/Auth; update button saves to /api/admin/settings. Screenshot shows section rendered after admin login."
      - working: true
        agent: "testing"
        comment: "✅ TESTED: Admin login works with password 'admin123'. Google reCAPTCHA 2.0 section renders with all inputs/toggles. Update button makes requests and saves settings. Backend properly validates keys when enabling toggles."

  - task: "Auth page: reCAPTCHA widget toggle"
    implemented: true
    working: true
    file: "/app/frontend/src/pages/AuthPage.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
      - working: true
        agent: "main"
        comment: "When enabled, registration shows reCAPTCHA widget and sends token to backend; login also sends token. Otherwise uses math captcha for register. Needs e2e test with real keys."
      - working: true
        agent: "testing"
        comment: "✅ TESTED: Auth page correctly switches between math captcha (when reCAPTCHA disabled) and reCAPTCHA widget (when enabled). Toggle functionality works through admin settings. Registration form shows appropriate captcha type based on settings."

metadata:
  created_by: "main_agent"
  version: "1.0"
  test_sequence: 1
  run_ui: true

test_plan:
  current_focus:
    - "Site fields on submissions/downloads"
    - "Home page: add Site column"
    - "Submit page: required site fields + reCAPTCHA widget toggle"
    - "Admin dashboard: reCAPTCHA keys + toggles"
    - "Auth page: reCAPTCHA widget toggle"
  stuck_tasks: []
  test_all: false
  test_priority: "high_first"

agent_communication:
  - agent: "main"
    message: "Implemented Site fields end-to-end and added optional Google reCAPTCHA v2 with admin-configurable keys + toggles for Submit and Auth. Please run backend+frontend tests focusing on toggles off (math captcha) and toggles on (reCAPTCHA) flows. Admin password for local UI: admin123 (as currently configured)."
  - agent: "testing"
    message: "TESTING COMPLETE: Found 1 critical issue with Site column display on home page. Site column header exists but shows 'SITE' instead of 'Site' in table headers. All other functionality working: site fields validation, reCAPTCHA toggle functionality, admin settings, and UI switching between math captcha and reCAPTCHA widget. Backend API returns site data correctly."