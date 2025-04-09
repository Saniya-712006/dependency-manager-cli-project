import requests
import subprocess
import json
from packaging import version
from packaging.specifiers import SpecifierSet
import re

# Function to get installed packages and their versions using pip
def get_installed_packages():
    result = subprocess.run(['pip', 'list', '--format', 'json'], stdout=subprocess.PIPE, text=True)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print("⚠ Error: Failed to parse installed packages.")
        return []

# Function to get package metadata from PyPI
def get_package_metadata(package_name, package_version):
    url = f"https://pypi.org/pypi/{package_name}/{package_version}/json"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

# Function to check if the package version is compatible with installed dependencies
def check_package_compatibility(package_name, new_version):
    metadata = get_package_metadata(package_name, new_version)
    
    if not metadata:
        print(f"⚠ Error: Could not fetch metadata for {package_name} {new_version}.")
        return False

    required_dependencies = metadata['info'].get('requires_dist', [])

    installed_packages = get_installed_packages()
    installed_versions = {pkg['name'].lower(): pkg['version'] for pkg in installed_packages}

    conflicts = []

    for dep in required_dependencies:
        dep_match = re.match(r"([\w\-]+)(.*)", dep)  # Extract package name and version range
        if not dep_match:
            continue  # Skip invalid dependency strings
        
        dep_name, dep_version_range = dep_match.groups()
        dep_name = dep_name.lower()
        dep_version_range = dep_version_range.strip()

        if dep_name in installed_versions:
            installed_version = installed_versions[dep_name]
            if not version_compatible(installed_version, dep_version_range):
                conflicts.append(f"❌ {dep_name} {installed_version} is incompatible with {dep_version_range}")

    if conflicts:
        print(f"⚠ Conflicts detected for {package_name} {new_version}:")
        for conflict in conflicts:
            print(f"   - {conflict}")
        return False

    return True

# Function to check if installed version satisfies required version range
def version_compatible(installed_version, required_version_range):
    try:
        if not required_version_range:
            return True  # No specific version requirement
        
        specifier = SpecifierSet(required_version_range)
        return version.parse(installed_version) in specifier
    except Exception as e:
        print(f"⚠ Error parsing version range '{required_version_range}': {e}")
        return False

# Function to check for any pip issues or broken dependencies
def check_pip_issues():
    result = subprocess.run(['pip', 'check'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.stdout:
        print(f"⚠ pip check found issues:\n{result.stdout.strip()}")

# Example usage
def main():
    check_pip_issues()

    package_name = 'numpy'  # Example package
    new_version = '1.21.0'  # Example version

    if not check_package_compatibility(package_name, new_version):
        print("❌ Upgrade will cause conflicts.")
    else:
        print("✅ Upgrade is safe.")

if __name__ == "__main__":
    main()