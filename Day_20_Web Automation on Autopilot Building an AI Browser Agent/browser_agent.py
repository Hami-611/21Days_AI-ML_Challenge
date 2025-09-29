import asyncio
import warnings
import os
import json
from dotenv import load_dotenv
from browser_use import Agent, ChatGoogle

load_dotenv()
warnings.filterwarnings("ignore", category=ResourceWarning)

async def main():
    task = "Search Google for 'what is browser automation' and tell me the top 3 results"
    llm = ChatGoogle(model="gemini-2.5-flash", api_key=os.getenv("GOOGLE_API_KEY"))
    agent = Agent(task=task, llm=llm)

    try:
        # Run agent
        result = await agent.run()

        # ---- Extract final text from result ----
        final_text = ""
        if hasattr(result, 'extracted_content'):
            final_text = result.extracted_content
        elif hasattr(result, 'summary'):
            final_text = result.summary
        elif hasattr(result, 'final_result'):
            final_text = result.final_result

        # ---- Extract URLs from browser history ----
        urls = []
        
        # Method 1: Try to get URLs from history if available
        if hasattr(agent.history, 'urls'):
            try:
                urls = agent.history.urls()
            except:
                urls = []
        
        # Method 2: Extract URLs from actions/events
        if not urls and hasattr(agent.history, 'actions'):
            for action in agent.history.actions:
                if hasattr(action, 'url'):
                    urls.append(action.url)
                # Check action data for URLs
                if hasattr(action, 'data'):
                    action_data = str(action.data)
                    if 'http' in action_data:
                        # Simple URL extraction from action data
                        import re
                        found_urls = re.findall(r'https?://[^\s\'\"]+', action_data)
                        urls.extend(found_urls)
        
        # Method 3: Extract from browser state if available
        if not urls and hasattr(agent, 'browser') and hasattr(agent.browser, 'current_page'):
            try:
                current_url = agent.browser.current_page.url
                if current_url:
                    urls.append(current_url)
            except:
                pass

        # Filter URLs
        filtered_urls = []
        for url in set(urls):  # Remove duplicates
            if (url and 
                url not in ("about:blank", "") and 
                "google.com/search" not in url.lower() and
                not url.startswith('data:')):
                filtered_urls.append(url)

        # ---- Print to console ----
        print("\n--- Agent Final Result ---")
        print(final_text)

        print("\n--- Filtered Browser History URLs ---")
        for url in filtered_urls:
            print(url)

        # ---- Save to file ----
        with open("history_urls.txt", "w", encoding="utf-8") as f:
            f.write("--- Agent Final Result ---\n")
            f.write(str(final_text) + "\n\n")
            f.write("--- Filtered Browser History URLs ---\n")
            for url in filtered_urls:
                f.write(url + "\n")
                
        # Also save detailed history for debugging
        with open("debug_history.json", "w", encoding="utf-8") as f:
            debug_info = {
                "final_text": str(final_text),
                "all_urls_found": list(set(urls)),
                "filtered_urls": filtered_urls,
                "history_attributes": dir(agent.history) if hasattr(agent.history, '__dir__') else []
            }
            json.dump(debug_info, f, indent=2)

        print(f"\n✅ Cleaned history saved to history_urls.txt")
        print(f"📊 Found {len(filtered_urls)} unique URLs after filtering")
        print(f"🔍 Debug info saved to debug_history.json")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Graceful shutdown
        try:
            if hasattr(agent, "shutdown"):
                await agent.shutdown()
            if hasattr(agent, "close"):
                await agent.close()
        except Exception as e:
            print(f"Warning during shutdown: {e}")
        await asyncio.sleep(0.1)

if __name__ == "__main__":
    asyncio.run(main())