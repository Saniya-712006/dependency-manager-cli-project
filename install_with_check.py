import requests
import subprocess
import json
import sys
from packaging import version

def get_installed_packages():
    """Fetch the list of installed packages and their versions."""
    result = subprocess.run(['pip', 'list', '--format', 'json'], stdout=subprocess.PIPE)
    return json.loads(result.stdout)

def get_package_metadata(package_name, package_version):
    """Fetch package metadata for a specific version from PyPI."""
    url = f"https://pypi.org/pypi/{package_name}/{package_version}/json"
    response = requests.get(url)
    return response.json() if response.status_code == 200 else None

def get_available_versions(package_name):
    """Fetch all available versions of a package from PyPI."""
    url = f"https://pypi.org/pypi/{package_name}/json"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return sorted(data["releases"].keys(), key=version.parse, reverse=True)
    return []

def check_package_compatibility(package_name, new_version, installed_packages, verbose=False):
    """Check if the specified package version is compatible with installed dependencies."""
    metadata = get_package_metadata(package_name, new_version)
    if not metadata:
        if verbose:
            print(f"⚠ Failed to fetch metadata for {package_name} {new_version}")
        return False

    required_dependencies = metadata['info'].get('requires_dist') or []
    installed_versions = {pkg['name'].lower(): pkg['version'] for pkg in installed_packages}

    conflicts = []
    for dep in required_dependencies:
        dep_parts = dep.split(" ")
        dep_name = dep_parts[0]
        dep_version_range = " ".join(dep_parts[1:]).strip("()")

        if dep_name.lower() in installed_versions:
            installed_version = installed_versions[dep_name.lower()]
            is_compatible = version_compatible(installed_version, dep_version_range)

            if verbose:
                print(f"🔍 Checking {dep_name}: Installed {installed_version}, Required {dep_version_range} → {'✅ Compatible' if is_compatible else '❌ Incompatible'}")

            if not is_compatible:
                conflicts.append(f"{dep_name} {installed_version} is incompatible with {dep_version_range}")

    if conflicts:
        if verbose:
            print(f"⚠ Conflicts detected for {package_name} {new_version}:")
            for conflict in conflicts:
                print(f"   ❌ {conflict}")
        return False

    return True

def version_compatible(installed_version, required_version_range):
    """Check if an installed version meets the required version constraints."""
    try:
        if '>' in required_version_range or '<' in required_version_range:
            return eval(f"version.parse('{installed_version}') {required_version_range}")
        else:
            return version.parse(installed_version) == version.parse(required_version_range)
    except Exception:
        return False

def find_best_compatible_version(package_name, installed_packages, verbose=False):
    """Find the best compatible version of a package based on installed dependencies."""
    available_versions = get_available_versions(package_name)

    if not available_versions:
        if verbose:
            print(f"❌ No versions found for {package_name}.")
        return None

    for ver in available_versions:
        if verbose:
            print(f"🔍 Checking version {ver} for compatibility...")
        if check_package_compatibility(package_name, ver, installed_packages, verbose):
            if verbose:
                print(f"✅ Found compatible version: {ver}")
            return ver

    if verbose:
        print(f"❌ No compatible version found for {package_name}.")
    return None

def main():
    """Main function to install a package with dependency checks."""
    if len(sys.argv) < 2:
        print("Usage: python install_with_check.py [-v] <package_name>")
        sys.exit(1)

    verbose = False
    args = sys.argv[1:]

    if "-v" in args:
        verbose = True
        args.remove("-v")

    package_name = args[0]

    # Get the list of installed packages
    installed_packages = get_installed_packages()

    # Find the best compatible version
    new_version = find_best_compatible_version(package_name, installed_packages, verbose)

    if not new_version:
        print("❌ No compatible version found. Installation aborted.")
        sys.exit(1)

    # Install the best compatible version
    print(f"✅ Installing {package_name} {new_version}...")
    try:
        subprocess.run(['pip', 'install', f"{package_name}=={new_version}"], check=True)
        print(f"✅ Successfully installed {package_name} {new_version}")
    except subprocess.CalledProcessError:
        print(f"❌ Installation failed for {package_name} {new_version}")

if __name__ == "__main__":
    main()