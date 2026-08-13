import json, glob, sys

# The IAM JSON policy grammar is a CLOSED set. Anything else is rejected with
# MalformedPolicyDocument, so a stray key makes the file unusable rather than merely untidy.
POLICY_KEYS = {'Version', 'Id', 'Statement'}
STMT_KEYS = {'Sid', 'Effect', 'Principal', 'NotPrincipal', 'Action', 'NotAction',
             'Resource', 'NotResource', 'Condition'}

bad = 0
for f in sorted(glob.glob('**/*.json', recursive=True)):
    try:
        d = json.load(open(f))
    except Exception as e:
        print(f'  INVALID JSON  {f}: {e}'); bad += 1; continue
    if not isinstance(d, dict) or 'Statement' not in d:
        continue
    for k in d:
        if k not in POLICY_KEYS:
            print(f'  BAD TOP KEY   {f}: {k!r}'); bad += 1
    stmts = d['Statement']
    if isinstance(stmts, dict): stmts = [stmts]
    for i, st in enumerate(stmts):
        for k in st:
            if k not in STMT_KEYS:
                print(f'  BAD STMT KEY  {f} statement[{i}]: {k!r}'); bad += 1
        if 'Effect' not in st:
            print(f'  MISSING Effect {f} statement[{i}]'); bad += 1
        # The alphanumeric-only Sid rule applies to IAM IDENTITY policies. Per the same AWS
        # grammar page, "other AWS services that support resource policies may have other
        # requirements ... some services allow additional characters such as spaces". A KMS key
        # policy is one: the AWS console itself generates Sids like
        # "Allow access for Key Administrators". A statement carrying a Principal is
        # resource-based, so the rule is applied only where it holds.
        #
        # This check was over-strict on its first run and flagged six valid KMS statements. That
        # is worth recording: a linter that reports valid input is worse than no linter, because
        # the next person "fixes" the input to satisfy it.
        sid = st.get('Sid')
        is_resource_policy = 'Principal' in st or 'NotPrincipal' in st
        if sid is not None and not is_resource_policy and not str(sid).isalnum():
            print(f'  NON-ALNUM Sid  {f} statement[{i}]: {sid!r} (IAM identity policies allow A-Za-z0-9 only)'); bad += 1
print(f'  policy files with problems: {bad}')
sys.exit(1 if bad else 0)
