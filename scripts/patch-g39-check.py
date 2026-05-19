#!/usr/bin/env python3
"""Patch script for G39 failure patterns (improved)"""

with open('bin/researchloop.js', 'r') as f:
    content = f.read()

# Check if cmdFailures already exists with clustering logic
has_clustering = 'clusterKey' in content and 'clusters[' in content
print("Already has clustering logic:", has_clustering)

if not has_clustering:
    # Need to add clustering function
    # Find the existing failures function
    idx = content.find('function cmdFailures() {')
    if idx == -1:
        print("ERROR: cmdFailures not found")
        exit(1)

    # Find the end of the function
    end_idx = content.find('\nfunction ', idx + 1)
    old_func = content[idx:end_idx]

    new_func = old_func  # Will be injected with clustering
    print("Would inject clustering into failures function")
else:
    print("cmdFailures already has clustering - skipping function injection")

# Check dispatch
if 'command === "failures")' not in content:
    print("ERROR: failures dispatch not found")
    exit(1)

# Check if we need to add the --top option (already has topN in existing code)
if 'topN = parseInt' not in content and 'topN =' not in content:
    print("Note: topN parsing may be missing")

print("G39 patch check complete")