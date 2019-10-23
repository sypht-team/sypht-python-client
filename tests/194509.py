import re, pyperclip

phoneRegex = re.compile(r'''
	(\d{3} | (\(\d{3}\)))?
	(\s|-|\.)?
	(\d{3})
	(\s|-|\.)
	(\d{4})
	(\s*(ext|x|ext.)\s*(\d{2,5}))?
	''',re.VERBOSE)

emailRegex = re.compile(r'''(
	[a-zA-Z0-9._%+-]+
	@
	[a-zA-Z]{2,8}
	(\.[a-zA-Z]{2,4})
	)''',re.VERBOSE)

text = str(pyperclip.paste())

matches = []

for groups in phoneRegex.findall(text):
	if groups[0]!='':
		phoneNum = '-'.join([groups[0],groups[3],groups[5]])
	else:
		phoneNum = '-'.join([groups[3],groups[5]])

	if groups[8] != '':
		phoneNum += ' x'+groups[8]
		
	matches.append(phoneNum)

for groups in emailRegex.findall(text):
	email = groups[0]
	matches.append(email)

if len(matches)>0:
	pyperclip.copy('\n'.join(matches))
	print('coppied to clipboard:')
	print('\n'.join(matches))
else:
	print('No matches found')
#print(phoneRegex.findall('222-444-5644  234.355.1345  123 234 1231 ext234'))
#print(emailRegex.findall('parthpant4@gmail.com'))
#print(matches)