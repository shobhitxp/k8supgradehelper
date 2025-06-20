from openai import OpenAI
import os

def analyze_deprecated_apis(pluto_data: list) -> str:
    # Check if OpenAI API key is set
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "⚠️ OpenAI API key not found. Please set OPENAI_API_KEY environment variable to get AI suggestions."
    
    # Handle empty results
    if not pluto_data or len(pluto_data) == 0:
        return "✅ No deprecated Kubernetes APIs found! Your manifests are up to date."
    
    # Check if pluto_data has the expected structure
    if isinstance(pluto_data, dict) and 'items' in pluto_data:
        items = pluto_data['items']
    elif isinstance(pluto_data, list):
        items = pluto_data
    else:
        items = [pluto_data]
    
    if not items:
        return "✅ No deprecated Kubernetes APIs found! Your manifests are up to date."
    
    # Create a detailed, customized prompt for Kubernetes API migration
    prompt = f"""
You are a senior Kubernetes DevOps engineer with 10+ years of experience in cluster migrations and API upgrades. Your task is to provide expert guidance for migrating deprecated Kubernetes APIs.

**DEPRECATED APIS DETECTED:**
{items}

**REQUIRED OUTPUT FORMAT:**

## 🔴 CRITICAL MIGRATION PLAN

### 1. **IMMEDIATE ACTION REQUIRED**
List each deprecated API with:
- 🔴 **Risk Level**: CRITICAL/HIGH/MEDIUM (based on removal timeline)
- 📅 **Removal Date**: When the API will be completely removed
- ⚡ **Migration Urgency**: Immediate/Within 30 days/Within 90 days

### 2. **MIGRATION EXECUTION PLAN**
For each deprecated API, provide:

#### **A. Before Migration (Current State)**
```yaml
# Current deprecated YAML
apiVersion: [DEPRECATED-VERSION]
kind: [RESOURCE-TYPE]
# ... rest of current config
```

#### **B. After Migration (Target State)**
```yaml
# Updated YAML with new API version
apiVersion: [NEW-VERSION]
kind: [RESOURCE-TYPE]
# ... rest of updated config
```

#### **C. Migration Commands**
```bash
# Step 1: Backup current resources
kubectl get [RESOURCE-TYPE] [NAME] -n [NAMESPACE] -o yaml > backup-[NAME].yaml

# Step 2: Apply updated YAML
kubectl apply -f updated-[NAME].yaml

# Step 3: Verify migration
kubectl get [RESOURCE-TYPE] [NAME] -n [NAMESPACE]
kubectl describe [RESOURCE-TYPE] [NAME] -n [NAMESPACE]
```

### 3. **VALIDATION CHECKLIST**
- [ ] Resource is running without errors
- [ ] No warnings in kubectl describe output
- [ ] All pods are in Running state
- [ ] Services are accessible
- [ ] Ingress rules are working (if applicable)

### 4. **ROLLBACK PROCEDURE**
```bash
# If migration fails, rollback immediately:
kubectl apply -f backup-[NAME].yaml
```

### 5. **COMMON ISSUES & SOLUTIONS**
- **Issue**: Resource stuck in Terminating state
  **Solution**: `kubectl patch [RESOURCE-TYPE] [NAME] -p '{{"metadata":{{"finalizers":[]}}}}' --type=merge`

- **Issue**: API version not recognized
  **Solution**: Check cluster version compatibility with `kubectl version`

### 6. **POST-MIGRATION VERIFICATION**
```bash
# Verify all resources are using new API versions
kubectl get all -o yaml | grep -E "apiVersion:|kind:"

# Check for any remaining deprecated APIs
kubectl api-resources --api-group=extensions
```

**IMPORTANT NOTES:**
- 🔴 **ALWAYS TEST IN STAGING FIRST**
- 🔴 **HAVE ROLLBACK PLAN READY**
- 🔴 **MONITOR RESOURCES AFTER MIGRATION**
- ✅ **USE VERSION CONTROL FOR ALL CHANGES**

Make this migration plan as practical and actionable as possible. Focus on immediate steps that can be executed right away.
"""
    
    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,  # Lower temperature for more consistent output
            max_tokens=2500
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ Error calling OpenAI API: {str(e)}"

