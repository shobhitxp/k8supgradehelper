import yaml
import os
import argparse
from pathlib import Path
from typing import Dict, List, Tuple

class KubernetesAPIMigrator:
    """Migrate deprecated Kubernetes API versions to their current equivalents."""
    
    # Mapping of deprecated API versions to their current equivalents
    API_MIGRATIONS = {
        # Deployments and other apps resources
        "extensions/v1beta1": {
            "Deployment": "apps/v1",
            "DaemonSet": "apps/v1", 
            "ReplicaSet": "apps/v1",
            "StatefulSet": "apps/v1",
            "Ingress": "networking.k8s.io/v1"
        },
        # Network Policies
        "networking.k8s.io/v1beta1": {
            "NetworkPolicy": "networking.k8s.io/v1"
        },
        # RBAC
        "rbac.authorization.k8s.io/v1beta1": {
            "ClusterRole": "rbac.authorization.k8s.io/v1",
            "ClusterRoleBinding": "rbac.authorization.k8s.io/v1",
            "Role": "rbac.authorization.k8s.io/v1",
            "RoleBinding": "rbac.authorization.k8s.io/v1"
        },
        # Storage
        "storage.k8s.io/v1beta1": {
            "StorageClass": "storage.k8s.io/v1",
            "CSIDriver": "storage.k8s.io/v1",
            "CSINode": "storage.k8s.io/v1"
        },
        # Admission
        "admissionregistration.k8s.io/v1beta1": {
            "MutatingWebhookConfiguration": "admissionregistration.k8s.io/v1",
            "ValidatingWebhookConfiguration": "admissionregistration.k8s.io/v1"
        }
    }
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.migration_log = []
    
    def migrate_yaml_file(self, input_file: str) -> Tuple[bool, str]:
        """Migrate a single YAML file and return success status and output path."""
        try:
            input_path = Path(input_file)
            if not input_path.exists():
                return False, f"Input file not found: {input_file}"
            
            # Read the YAML file
            with open(input_path, 'r') as f:
                content = f.read()
            
            # Split into multiple documents if it's a multi-doc YAML
            documents = list(yaml.safe_load_all(content))
            
            migrated_docs = []
            changes_made = False
            
            for doc in documents:
                if doc is None:
                    continue
                    
                migrated_doc, doc_changed = self._migrate_document(doc)
                migrated_docs.append(migrated_doc)
                if doc_changed:
                    changes_made = True
            
            if not changes_made:
                return True, f"No migrations needed for {input_file}"
            
            # Write migrated content to output directory
            output_file = self.output_dir / f"{input_path.stem}.migrated{input_path.suffix}"
            with open(output_file, 'w') as f:
                yaml.dump_all(migrated_docs, f, default_flow_style=False, sort_keys=False)
            
            self.migration_log.append(f"✅ Migrated: {input_file} -> {output_file}")
            return True, str(output_file)
            
        except Exception as e:
            error_msg = f"Error migrating {input_file}: {str(e)}"
            self.migration_log.append(f"❌ {error_msg}")
            return False, error_msg
    
    def _migrate_document(self, doc: Dict) -> Tuple[Dict, bool]:
        """Migrate a single YAML document and return the migrated doc and whether changes were made."""
        if not isinstance(doc, dict):
            return doc, False
        
        # Check if this is a Kubernetes resource
        api_version = doc.get('apiVersion', '')
        kind = doc.get('kind', '')
        
        if not api_version or not kind:
            return doc, False
        
        # Check if this API version needs migration
        for deprecated_version, migrations in self.API_MIGRATIONS.items():
            if api_version == deprecated_version and kind in migrations:
                new_api_version = migrations[kind]
                doc['apiVersion'] = new_api_version
                
                # Handle special cases for different resource types
                if kind == "Ingress" and new_api_version == "networking.k8s.io/v1":
                    doc = self._migrate_ingress_v1(doc)
                
                self.migration_log.append(f"  🔄 {kind}: {api_version} -> {new_api_version}")
                return doc, True
        
        return doc, False
    
    def _migrate_ingress_v1(self, ingress: Dict) -> Dict:
        """Handle special migration for Ingress v1 (adds required pathType)."""
        if 'spec' in ingress and 'rules' in ingress['spec']:
            for rule in ingress['spec']['rules']:
                if 'http' in rule and 'paths' in rule['http']:
                    for path in rule['http']['paths']:
                        # Add pathType if not present (required in v1)
                        if 'pathType' not in path:
                            path['pathType'] = 'Prefix'
                        
                        # Update backend structure
                        if 'backend' in path and 'serviceName' in path['backend']:
                            # Convert old backend format to new
                            old_backend = path['backend']
                            path['backend'] = {
                                'service': {
                                    'name': old_backend['serviceName'],
                                    'port': {
                                        'number': old_backend.get('servicePort', 80)
                                    }
                                }
                            }
        
        return ingress
    
    def migrate_directory(self, input_dir: str) -> List[str]:
        """Migrate all YAML files in a directory."""
        input_path = Path(input_dir)
        if not input_path.exists():
            return [f"Directory not found: {input_dir}"]
        
        yaml_files = list(input_path.glob("*.yaml")) + list(input_path.glob("*.yml"))
        results = []
        
        for yaml_file in yaml_files:
            success, message = self.migrate_yaml_file(str(yaml_file))
            results.append(message)
        
        return results
    
    def get_migration_summary(self) -> str:
        """Get a summary of all migrations performed."""
        if not self.migration_log:
            return "No migrations performed."
        
        return "\n".join(self.migration_log)

def main():
    parser = argparse.ArgumentParser(description="Migrate deprecated Kubernetes API versions in YAML files")
    parser.add_argument("input", help="Input YAML file or directory")
    parser.add_argument("--output-dir", "-o", default="output", help="Output directory (default: output)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    migrator = KubernetesAPIMigrator(args.output_dir)
    
    input_path = Path(args.input)
    
    if input_path.is_file():
        # Migrate single file
        success, message = migrator.migrate_yaml_file(args.input)
        print(message)
    elif input_path.is_dir():
        # Migrate all YAML files in directory
        results = migrator.migrate_directory(args.input)
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