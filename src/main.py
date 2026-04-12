import os, requests
from kubernetes import client, config, watch
import google.generativeai as genai

# Setup
PLATFORM = os.getenv("NOTIFY_PLATFORM", "teams")
CLOUD = os.getenv("CLOUD_PROVIDER", "gcp")
genai.configure(api_key=os.getenv("GEMINI_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

def get_ai_analysis(pod, logs):
    prompt = f"Pod {pod} on {CLOUD} crashed. Logs: {logs}. Provide a 1-sentence fix."
    return model.generate_content(prompt).text

def send_alert(text):
    url = os.getenv("WEBHOOK_URL")
    requests.post(url, json={"text": text})

def main():
    try: config.load_incluster_config()
    except: config.load_kube_config()
    
    v1 = client.CoreV1Api()
    w = watch.Watch()
    for event in w.stream(v1.list_event_for_all_namespaces):
        if event['object'].reason == "BackOff":
            pod = event['object'].involved_object.name
            ns = event['object'].involved_object.namespace
            logs = v1.read_namespaced_pod_log(name=pod, namespace=ns, tail_lines=20)
            analysis = get_ai_analysis(pod, logs)
            send_alert(f"🚨 {CLOUD} Alert: {analysis}")

if __name__ == "__main__":
    main()
