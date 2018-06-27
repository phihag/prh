#!/usr/bin/env python3

import json
import os.path
import re
import subprocess
import urllib.error
import urllib.parse
import urllib.request

def main():
	with open(os.path.expanduser('~/.glpr-token'), 'r', encoding='ascii') as tokf:
		token = tokf.read().strip()

	branch_b = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'])
	branch = branch_b.decode('utf-8').strip()
	print('git push -u origin %s' % branch)
	subprocess.check_call(['git', 'push', '-u', 'origin', branch])

	remote_url_b = subprocess.check_output(['git', 'remote', 'get-url', 'origin'])
	remote_url = remote_url_b.decode('utf-8').strip()
	m = re.match(
		r'git@(?P<domain>[^:]+):(?P<group>[^/]+)/(?P<project>[^/]+)\.git$', remote_url)
	if not m:
		raise ValueError('Cannot parse remote URL %s' % remote_url)

	commit_desc_b = subprocess.check_output(['git', 'log', '-1', '--pretty=%B'])
	commit_desc = commit_desc_b.decode('utf-8').strip()
	desc_lines = commit_desc.splitlines()
	title = desc_lines[0]
	assert title
	desc = '\n'.join(desc_lines[1:])

	params = {
		'source_branch': branch,
		'target_branch': 'master',
		'title': title,
		'description': desc,
		'remove_source_branch': True,
	}
	base_url = 'https://' + m.group('domain')
	project_id = m.group('group') + '/' + m.group('project')
	print('Creating PR ... ', end='')
	api_url = base_url + '/api/v4/projects/%s/merge_requests' % urllib.parse.quote_plus(project_id)
	req = urllib.request.Request(
		api_url,
		data=json.dumps(params).encode('utf-8'),
		headers={
			'content-type': 'application/json',
			'PRIVATE-TOKEN': token,
		})
	try:
		response = urllib.request.urlopen(req)
	except urllib.error.HTTPError as he:
		if he.code == 409:  # Conflict
			print('exists already! Look on %s/%s/merge_requests' %
				(base_url, project_id))
		else:
			raise
	else:
		response_data = json.loads(response.read())
		web_url = response_data['web_url']
		print(web_url)

if __name__ == '__main__':
	main()
