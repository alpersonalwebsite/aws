import json, glob, sys

# The IAM JSON policy grammar is a CLOSED set. Anything else is rejected with
# MalformedPolicyDocument, so a stray key makes the file unusable rather than merely untidy.
POLICY_KEYS = {'Version', 'Id', 'Statement'}
STMT_KEYS = {'Sid', 'Effect', 'Principal', 'NotPrincipal', 'Action', 'NotAction',
             'Resource', 'NotResource', 'Condition'}
VALID_VERSIONS = {'2008-10-17', '2012-10-17'}

bad = 0


def problem(msg):
    global bad
    print(f'  {msg}')
    bad += 1


for f in sorted(glob.glob('**/*.json', recursive=True)):
    try:
        d = json.load(open(f))
    except Exception as e:
        problem(f'INVALID JSON   {f}: {e}')
        continue
    if not isinstance(d, dict) or 'Statement' not in d:
        continue

    for k in d:
        if k not in POLICY_KEYS:
            problem(f'BAD TOP KEY    {f}: {k!r}')
    if 'Version' in d and d['Version'] not in VALID_VERSIONS:
        problem(f'BAD Version    {f}: {d["Version"]!r} (only {sorted(VALID_VERSIONS)})')

    stmts = d['Statement']
    if isinstance(stmts, dict):
        stmts = [stmts]
    if not isinstance(stmts, list):
        problem(f'BAD Statement  {f}: must be an object or a list, got {type(stmts).__name__}')
        continue
    # An empty Statement list parses as JSON and is rejected by IAM. The first version of this
    # checker returned success for it, which is the vacuous pass a linter exists to prevent.
    if not stmts:
        problem(f'EMPTY Statement {f}: a policy needs at least one statement')
        continue

    for i, st in enumerate(stmts):
        # Guard the type BEFORE touching keys. A non-object statement used to raise
        # AttributeError and abort the whole run, so one malformed file hid every other file.
        if not isinstance(st, dict):
            problem(f'BAD STMT TYPE  {f} statement[{i}]: {type(st).__name__}, expected an object')
            continue

        for k in st:
            if k not in STMT_KEYS:
                problem(f'BAD STMT KEY   {f} statement[{i}]: {k!r}')

        # Effect must be present AND one of two literals. Checking only presence let
        # "Effect": "allow" through, which IAM rejects for case.
        eff = st.get('Effect')
        if eff is None:
            problem(f'MISSING Effect {f} statement[{i}]')
        elif eff not in ('Allow', 'Deny'):
            problem(f'BAD Effect     {f} statement[{i}]: {eff!r} (must be "Allow" or "Deny")')

        # Exactly one of Action / NotAction. Neither means the statement grants nothing and
        # IAM rejects it; both is also invalid.
        has_a, has_na = 'Action' in st, 'NotAction' in st
        if has_a and has_na:
            problem(f'BOTH Action    {f} statement[{i}]: Action and NotAction are exclusive')
        elif not has_a and not has_na:
            problem(f'NO Action      {f} statement[{i}]: needs Action or NotAction')

        # Resource is required in identity policies. In a resource policy the resource is
        # implicit (a KMS key policy scopes to its own key), so it is only required when there
        # is no Principal.
        is_resource_policy = 'Principal' in st or 'NotPrincipal' in st
        if not is_resource_policy and not ('Resource' in st or 'NotResource' in st):
            problem(f'NO Resource    {f} statement[{i}]: identity policies need Resource')

        # The alphanumeric-only Sid rule applies to IAM IDENTITY policies. Per the AWS grammar
        # page, "other AWS services that support resource policies may have other requirements
        # ... some services allow additional characters such as spaces". A KMS key policy is
        # one: the AWS console itself generates Sids like "Allow access for Key Administrators".
        #
        # This check was over-strict on its first run and flagged six valid KMS statements. That
        # is worth recording: a linter that reports valid input is worse than no linter, because
        # the next person "fixes" the input to satisfy it.
        sid = st.get('Sid')
        if sid is not None and not is_resource_policy and not str(sid).isalnum():
            problem(f'NON-ALNUM Sid  {f} statement[{i}]: {sid!r} '
                    '(IAM identity policies allow A-Za-z0-9 only)')

print(f'  policy files with problems: {bad}')
sys.exit(1 if bad else 0)
