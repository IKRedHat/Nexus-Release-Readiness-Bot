<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nexus Engineering Onboarding Guide</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
        
        body {
            font-family: 'Inter', sans-serif;
            color: #1f2937;
            background-color: #f9fafb;
            line-height: 1.6;
        }

        h1, h2, h3 { color: #111827; }
        
        /* Table Styling */
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 1.5rem 0;
            background-color: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
        }
        
        th {
            background-color: #f3f4f6;
            text-align: left;
            padding: 12px 16px;
            font-weight: 600;
            color: #374151;
            border-bottom: 1px solid #e5e7eb;
        }
        
        td {
            padding: 12px 16px;
            border-bottom: 1px solid #e5e7eb;
            color: #4b5563;
        }
        
        tr:last-child td { border-bottom: none; }
        tr:hover { background-color: #f9fafb; }

        /* Code Block Styling */
        pre {
            background-color: #1e293b;
            color: #e2e8f0;
            padding: 1rem;
            border-radius: 0.5rem;
            overflow-x: auto;
            font-family: monospace;
            margin: 1rem 0;
        }

        code {
            background-color: #f3f4f6;
            color: #db2777; /* Pinkish red for inline code */
            padding: 0.2rem 0.4rem;
            border-radius: 0.25rem;
            font-family: monospace;
            font-size: 0.875em;
        }

        pre code {
            background-color: transparent;
            color: inherit;
            padding: 0;
        }

        /* Blockquote Styling */
        blockquote {
            border-left: 4px solid #3b82f6;
            background-color: #eff6ff;
            padding: 1rem;
            margin: 1.5rem 0;
            border-radius: 0 0.5rem 0.5rem 0;
            color: #1e3a8a;
        }
    </style>
</head>
<body class="py-10 px-4 md:px-8">

    <div class="max-w-4xl mx-auto bg-white p-8 md:p-12 rounded-xl shadow-lg border border-gray-200">
        
        <!-- Header -->
        <div class="text-center mb-10 border-b pb-8 border-gray-200">
            <h1 class="text-4xl font-extrabold mb-4 text-gray-900">🧭 Nexus Engineering Onboarding Guide</h1>
            <p class="text-lg text-gray-600 mb-6">The comprehensive map to the Nexus Multi-Agent Release Automation Platform.</p>
            
            <div class="flex justify-center gap-2 flex-wrap">
                <img src="https://img.shields.io/badge/Status-Active_Development-blue?style=for-the-badge" alt="Status">
                <img src="https://img.shields.io/badge/Tech-Python_|_FastAPI_|_LangGraph-green?style=for-the-badge" alt="Tech">
                <img src="https://img.shields.io/badge/Docs-Up_to_Date-orange?style=for-the-badge" alt="Docs">
            </div>
        </div>

        <!-- Section 1 -->
        <section class="mb-12">
            <h2 class="text-2xl font-bold mb-4 pb-2 border-b border-gray-200">1. 🚀 What is Nexus? (The 30-Second Pitch)</h2>
            
            <blockquote>
                <strong>Think of Nexus as a super-smart Release Manager that lives in Slack.</strong>
            </blockquote>

            <p class="mb-4">Instead of you manually checking 5 different tools, Nexus orchestrates the work:</p>
            <ol class="list-decimal pl-6 space-y-2 mb-4 text-gray-700">
                <li><strong>🧠 Thinks:</strong> "User asked for status -> I need to check Jira and Jenkins."</li>
                <li><strong>⚡ Acts:</strong> Securely connects to tools via API.</li>
                <li><strong>📝 Summarizes:</strong> Returns a "Go/No-Go" decision report.</li>
            </ol>
            
            <p class="text-gray-700"><strong>It's not just a chatbot.</strong> It is a <strong>Stateful Multi-Agent System</strong> capable of reasoning, planning, and executing complex workflows.</p>
        </section>

        <!-- Section 2 -->
        <section class="mb-12">
            <h2 class="text-2xl font-bold mb-4 pb-2 border-b border-gray-200">2. 🏗️ The Architecture: Hub-and-Spoke</h2>
            <p class="mb-4 text-gray-700">We use a <strong>Monorepo</strong> structure organized like a wheel.</p>

            <table>
                <thead>
                    <tr>
                        <th class="w-1/4">Component</th>
                        <th class="w-1/4">Role</th>
                        <th>Description</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><strong>The Hub</strong></td>
                        <td>🧠 <strong>Orchestrator</strong></td>
                        <td>The central brain. Receives Slack messages, plans the workflow using AI, and delegates tasks.</td>
                    </tr>
                    <tr>
                        <td><strong>The Spokes</strong></td>
                        <td>🤖 <strong>Agents</strong></td>
                        <td>Small, focused services. Each agent handles ONE tool (Jira, Git, etc.) and reports back to the Hub.</td>
                    </tr>
                </tbody>
            </table>
        </section>

        <!-- Section 3 -->
        <section class="mb-12">
            <h2 class="text-2xl font-bold mb-4 pb-2 border-b border-gray-200">3. 📂 Navigating the Code (<code>/services</code>)</h2>
            <p class="mb-6 text-gray-700">This is where 90% of your work will happen. Each folder acts as an independent microservice.</p>

            <h3 class="text-xl font-semibold mb-2 text-indigo-600">🧠 The Brain</h3>
            <ul class="list-disc pl-6 mb-6 text-gray-700 space-y-1">
                <li><strong><code>services/orchestrator/</code></strong>
                    <ul class="list-circle pl-6 mt-1 text-gray-600">
                        <li><strong>Role:</strong> The decision maker. Maintains memory and runs the reasoning loop.</li>
                        <li><strong>Key File:</strong> <code>app/core/react_engine.py</code> (The AI Logic).</li>
                        <li><strong>Tech:</strong> Python, FastAPI, Gemini AI, LangGraph.</li>
                    </ul>
                </li>
            </ul>

            <h3 class="text-xl font-semibold mb-2 text-cyan-600">🤖 The Hands (Agents)</h3>
            <p class="mb-2 text-gray-700">These services wrap external APIs into a standard interface.</p>
            
            <table>
                <thead>
                    <tr>
                        <th class="w-1/3">Agent</th>
                        <th>Purpose</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><code>jira_agent/</code></td>
                        <td>Translates "Get Ticket" into Atlassian API calls. Handles hierarchy fetching.</td>
                    </tr>
                    <tr>
                        <td><code>git_ci_agent/</code></td>
                        <td>Triggers Jenkins builds, checks GitHub PR status, and runs RCA.</td>
                    </tr>
                    <tr>
                        <td><code>slack_agent/</code></td>
                        <td>The "Ears". Listens to Slack events/commands and forwards them to the Hub.</td>
                    </tr>
                    <tr>
                        <td><code>reporting_agent/</code></td>
                        <td>Generates beautiful HTML dashboards and publishes them to Confluence.</td>
                    </tr>
                </tbody>
            </table>

            <h3 class="text-xl font-semibold mb-2 mt-6 text-gray-600">⚙️ The Control Panel</h3>
            <ul class="list-disc pl-6 mb-4 text-gray-700">
                <li><strong><code>services/admin_dashboard/</code></strong>
                    <ul class="list-circle pl-6 mt-1 text-gray-600">
                        <li><strong>Role:</strong> A web UI to manage API keys and configurations without restarting servers.</li>
                        <li><strong>Tech:</strong> React (Frontend) + FastAPI (Backend).</li>
                    </ul>
                </li>
            </ul>
        </section>

        <!-- Section 4 -->
        <section class="mb-12">
            <h2 class="text-2xl font-bold mb-4 pb-2 border-b border-gray-200">4. 🔗 The Glue (<code>/shared</code>)</h2>
            <p class="mb-4 text-gray-700">We hate repeating code. Common logic lives here to keep agents lightweight.</p>
            
            <ul class="space-y-4">
                <li class="bg-gray-50 p-4 rounded border border-gray-200">
                    <div class="font-bold text-gray-800 mb-1">📦 <code>shared/nexus_lib/schemas/</code></div>
                    <div class="text-gray-600"><strong>The Contracts:</strong> Defines data models like <code>JiraTicket</code>. Ensures the Orchestrator and Agents speak the same language.</div>
                </li>
                <li class="bg-gray-50 p-4 rounded border border-gray-200">
                    <div class="font-bold text-gray-800 mb-1">🛡️ <code>shared/nexus_lib/middleware.py</code></div>
                    <div class="text-gray-600"><strong>Security & Metrics:</strong> Automatically handles token validation and request counting for every service.</div>
                </li>
            </ul>
        </section>

        <!-- Section 5 -->
        <section class="mb-12">
            <h2 class="text-2xl font-bold mb-4 pb-2 border-b border-gray-200">5. 🛠️ How It Runs (<code>/infrastructure</code>)</h2>
            <p class="mb-4 text-gray-700">We use <strong>Docker</strong> to containerize everything. No "it works on my machine" issues.</p>
            
            <div class="bg-slate-800 text-white p-6 rounded-lg shadow-inner">
                <h3 class="text-xl font-mono mb-4 border-b border-gray-600 pb-2">docker-compose.yml</h3>
                <p class="mb-4 text-gray-300">This magic file spins up the entire world with one command:</p>
                <ol class="list-decimal pl-6 space-y-2 text-gray-300">
                    <li>🗄️ <strong>Postgres:</strong> For saving state (Memory).</li>
                    <li>⚡ <strong>Redis:</strong> For fast configuration caching.</li>
                    <li>🚀 <strong>Orchestrator + 5 Agents:</strong> All connected on a private network.</li>
                </ol>
            </div>
        </section>

        <!-- Section 6 -->
        <section class="mb-12">
            <h2 class="text-2xl font-bold mb-4 pb-2 border-b border-gray-200">6. 💻 Your First Contribution</h2>
            <p class="mb-6 text-gray-700">Ready to ship code? Follow this flow:</p>

            <ol class="list-decimal pl-6 space-y-4 text-gray-700 marker:font-bold marker:text-blue-600">
                <li>
                    <strong>Pick a Card:</strong> Find a Jira ticket (e.g., <em>"Add support for Trello"</em>).
                </li>
                <li>
                    <strong>Create the Agent:</strong>
                    <ul class="list-disc pl-6 mt-1 text-gray-600">
                        <li>Copy the <code>jira_agent</code> folder.</li>
                        <li>Rename it to <code>trello_agent</code>.</li>
                    </ul>
                </li>
                <li>
                    <strong>Define the Contract:</strong> Go to <code>shared/nexus_lib/schemas</code> and define what a <code>TrelloCard</code> looks like.
                </li>
                <li>
                    <strong>Implement Logic:</strong> Write the code to talk to Trello API using our <code>AsyncHttpClient</code> wrapper.
                </li>
                <li>
                    <strong>Register:</strong> Add the agent to <code>docker-compose.yml</code> and tell the Orchestrator about the new tool.
                </li>
                <li>
                    <strong>Test:</strong>
                    <pre><code>./setup_local_env.sh
docker-compose up</code></pre>
                </li>
            </ol>

            <div class="mt-8 p-4 bg-yellow-50 border border-yellow-200 rounded-lg text-yellow-800 flex items-start gap-3">
                <i class="fas fa-lightbulb mt-1 text-yellow-500"></i>
                <div>
                    <strong>Pro Tip:</strong> Stuck? Check <code>tests/e2e/</code>. We have end-to-end tests that trace a request from start to finish!
                </div>
            </div>
        </section>

    </div>

</body>
</html>
