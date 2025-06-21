import yaml
import os
import argparse
from pathlib import Path
from typing import Dict, List, Tuple
from openai import OpenAI
import json

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Using system environment variables.")

class LLMYAMLMigrator:
    """Use LLM to intelligently migrate deprecated Kubernetes API versions in YAML files."""
    
    def __init__(self, output_dir: str = "output", api_key: str = None):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.migration_log = []
        
        # Initialize OpenAI client
        if not api_key:
            api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
        
        self.client = OpenAI(api_key=api_key)
    
    def migrate_yaml_file(self, input_file: str) -> Tuple[bool, str]:
        """Migrate a single YAML file using LLM and return success status and output path."""
        try:
            input_path = Path(input_file)
            if not input_path.exists():
                return False, f"Input file not found: {input_file}"
            
            # Read the YAML file
            with open(input_path, 'r') as f:
                content = f.read()
            
            # Use LLM to migrate the YAML
            migrated_content = self._migrate_with_llm(content)
            
            if migrated_content == content:
                return True, f"No migrations needed for {input_file}"
            
            # Write migrated content to output directory
            output_file = self.output_dir / f"{input_path.stem}.llm-migrated{input_path.suffix}"
            with open(output_file, 'w') as f:
                f.write(migrated_content)
            
            self.migration_log.append(f"✅ LLM Migrated: {input_file} -> {output_file}")
            return True, str(output_file)
            
        except Exception as e:
            error_msg = f"Error migrating {input_file}: {str(e)}"
            self.migration_log.append(f"❌ {error_msg}")
            return False, error_msg
    
    def _migrate_with_llm(self, yaml_content: str) -> str:
        """Use LLM to migrate YAML content."""
        
        prompt = f"""
You are a Kubernetes expert specializing in API migrations. Your task is to migrate deprecated Kubernetes API versions to their current equivalents.

**INPUT YAML:**
```yaml
{yaml_content}
```

**MIGRATION RULES:**
1. **Deployments, DaemonSets, ReplicaSets, StatefulSets**: `extensions/v1beta1` → `apps/v1`
2. **Ingress**: `extensions/v1beta1` → `networking.k8s.io/v1`
   - Add required `pathType: Prefix` to each path
   - Convert backend from `serviceName/servicePort` to `service.name/service.port.number`
3. **NetworkPolicy**: `networking.k8s.io/v1beta1` → `networking.k8s.io/v1`
4. **RBAC resources**: `rbac.authorization.k8s.io/v1beta1` → `rbac.authorization.k8s.io/v1`
5. **Storage resources**: `storage.k8s.io/v1beta1` → `storage.k8s.io/v1`
6. **Admission resources**: `admissionregistration.k8s.io/v1beta1` → `admissionregistration.k8s.io/v1`

**REQUIREMENTS:**
- Only change the `apiVersion` field and any required structural changes
- Preserve all other fields exactly as they are
- Maintain the same YAML structure and formatting
- Handle multi-document YAML files (separated by `---`)
- Ensure the output is valid YAML
- Add any required fields that are mandatory in the new API version

**OUTPUT FORMAT:**
Return ONLY the migrated YAML content, no explanations or markdown formatting.

**EXAMPLE:**
If input has `apiVersion: extensions/v1beta1` and `kind: Deployment`, output should have `apiVersion: apps/v1` and `kind: Deployment`.

Migrate the YAML now:
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",  # Use GPT-4 for better YAML understanding
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,  # Low temperature for consistent output
                max_tokens=4000
            )
            
            migrated_yaml = response.choices[0].message.content.strip()
            
            # Clean up the response (remove markdown if present)
            if migrated_yaml.startswith("```yaml"):
                migrated_yaml = migrated_yaml.split("```yaml", 1)[1]
            if migrated_yaml.startswith("```"):
                migrated_yaml = migrated_yaml.split("```", 1)[1]
            if migrated_yaml.endswith("```"):
                migrated_yaml = migrated_yaml.rsplit("```", 1)[0]
            
            migrated_yaml = migrated_yaml.strip()
            
            # Validate that the output is valid YAML
            try:
                yaml.safe_load_all(migrated_yaml)
                return migrated_yaml
            except yaml.YAMLError as e:
                self.migration_log.append(f"⚠️ LLM output validation failed: {str(e)}")
                # Fall back to original content if LLM output is invalid
                return yaml_content
                
        except Exception as e:
            self.migration_log.append(f"⚠️ LLM migration failed: {str(e)}")
            return yaml_content
    
    def migrate_with_analysis(self, input_file: str) -> Tuple[bool, str, str]:
        """Migrate YAML and provide detailed analysis of changes."""
        try:
            input_path = Path(input_file)
            if not input_path.exists():
                return False, f"Input file not found: {input_file}", ""
            
            # Read the YAML file
            with open(input_path, 'r') as f:
                content = f.read()
            
            # Get detailed analysis and migration
            analysis_prompt = f"""
You are a Kubernetes expert. Analyze this YAML file and provide a detailed migration plan.

**INPUT YAML:**
```yaml
{content}
```

**TASK:**
1. Identify all deprecated API versions
2. Provide the exact changes needed
3. Give the migrated YAML
4. Explain what changed and why

**OUTPUT FORMAT:**
Return a JSON object with the following structure:
{{
    "deprecated_apis": [
        {{
            "kind": "Deployment",
            "old_version": "extensions/v1beta1",
            "new_version": "apps/v1",
            "changes_needed": ["Update apiVersion", "Add required fields"]
        }}
    ],
    "migrated_yaml": "the complete migrated YAML content",
    "analysis": "detailed explanation of what changed and why",
    "warnings": ["any potential issues or breaking changes"]
}}
"""
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": analysis_prompt}],
                temperature=0.1,
                max_tokens=4000
            )
            
            try:
                result = json.loads(response.choices[0].message.content.strip())
                
                # Write migrated content
                output_file = self.output_dir / f"{input_path.stem}.analyzed-migrated{input_path.suffix}"
                with open(output_file, 'w') as f:
                    f.write(result["migrated_yaml"])
                
                # Write analysis report
                analysis_file = self.output_dir / f"{input_path.stem}.analysis.md"
                with open(analysis_file, 'w') as f:
                    f.write(f"# Migration Analysis for {input_path.name}\n\n")
                    f.write(f"## Deprecated APIs Found\n")
                    for api in result["deprecated_apis"]:
                        f.write(f"- **{api['kind']}**: {api['old_version']} → {api['new_version']}\n")
                        f.write(f"  - Changes: {', '.join(api['changes_needed'])}\n\n")
                    f.write(f"## Analysis\n{result['analysis']}\n\n")
                    if result.get("warnings"):
                        f.write(f"## Warnings\n")
                        for warning in result["warnings"]:
                            f.write(f"- {warning}\n")
                
                self.migration_log.append(f"✅ Analyzed & Migrated: {input_file} -> {output_file}")
                return True, str(output_file), str(analysis_file)
                
            except json.JSONDecodeError:
                # Fall back to simple migration if JSON parsing fails
                return self.migrate_yaml_file(input_file), "", ""
                
        except Exception as e:
            error_msg = f"Error in analysis migration {input_file}: {str(e)}"
            self.migration_log.append(f"❌ {error_msg}")
            return False, error_msg, ""
    
    def migrate_directory(self, input_dir: str, with_analysis: bool = False) -> List[str]:
        """Migrate all YAML files in a directory."""
        input_path = Path(input_dir)
        if not input_path.exists():
            return [f"Directory not found: {input_dir}"]
        
        yaml_files = list(input_path.glob("*.yaml")) + list(input_path.glob("*.yml"))
        results = []
        
        for yaml_file in yaml_files:
            if with_analysis:
                success, output_file, analysis_file = self.migrate_with_analysis(str(yaml_file))
                if success:
                    results.append(f"✅ {yaml_file.name} -> {output_file}")
                    if analysis_file:
                        results.append(f"📊 Analysis: {analysis_file}")
                else:
                    results.append(f"❌ {yaml_file.name}: {output_file}")
            else:
                success, message = self.migrate_yaml_file(str(yaml_file))
                results.append(message)
        
        return results
    
    def get_migration_summary(self) -> str:
        """Get a summary of all migrations performed."""
        if not self.migration_log:
            return "No migrations performed."
        
        return "\n".join(self.migration_log)

def main():
    parser = argparse.ArgumentParser(description="Use LLM to migrate deprecated Kubernetes API versions in YAML files")
    parser.add_argument("input", help="Input YAML file or directory")
    parser.add_argument("--output-dir", "-o", default="output", help="Output directory (default: output)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--analysis", "-a", action="store_true", help="Generate detailed analysis report")
    parser.add_argument("--api-key", help="OpenAI API key (or set OPENAI_API_KEY env var)")
    
    args = parser.parse_args()
    
    try:
        migrator = LLMYAMLMigrator(args.output_dir, args.api_key)
    except ValueError as e:
        print(f"Error: {e}")
        return 1
    
    input_path = Path(args.input)
    
    if input_path.is_file():
        # Migrate single file
        if args.analysis:
            success, output_file, analysis_file = migrator.migrate_with_analysis(args.input)
            if success:
                print(f"✅ Migrated: {output_file}")
                if analysis_file:
                    print(f"📊 Analysis: {analysis_file}")
            else:
                print(f"❌ Failed: {output_file}")
        else:
            success, message = migrator.migrate_yaml_file(args.input)
            print(message)
    elif input_path.is_dir():
        # Migrate all YAML files in directory
        results = migrator.migrate_directory(args.input, args.analysis)
        for result in results:
            print(result)
    else:
        print(f"Error: {args.input} is not a valid file or directory")
        return 1
    
    if args.verbose:
        print("\n" + "="*50)
        print("MIGRATION SUMMARY:")
        print("="*50)
        print(migrator.get_migration_summary())
    
    return 0

if __name__ == "__main__":
    exit(main()) 