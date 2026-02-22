from src.agent import Agent

agent = Agent()
print('Searching forums for updated keywords...\n')

results = agent.search_all_sources()
print(f'✓ Total results found: {len(results)}')

# Group by source
sources = {}
for item in results:
    src = item.get('source', 'unknown')
    if src not in sources:
        sources[src] = []
    sources[src].append(item)

print('\nResults by source:')
for src in sorted(sources.keys()):
    items = sources[src]
    print(f'\n{src}: {len(items)} items')
    for item in items[:3]:
        print(f'  - {item["title"][:60]}')
        if len(items) > 3:
            print(f'  ... and {len(items)-3} more')
            break
