# CI/CD Pipeline Configuration Samples

## GitHub Actions: Full CI/CD Workflow

```yaml
name: CI/CD Pipeline
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  id-token: write
  contents: read

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v6
    - uses: actions/setup-node@v6
      with:
        node-version: 20
        cache: pnpm
    - run: pnpm install --frozen-lockfile
    - run: pnpm lint

  test:
    runs-on: ubuntu-latest
    needs: [lint]
    strategy:
      matrix:
        node-version: [18, 20, 22]
    steps:
    - uses: actions/checkout@v6
    - uses: actions/setup-node@v6
      with:
        node-version: ${{ matrix.node-version }}
        cache: pnpm
    - run: pnpm install --frozen-lockfile
    - run: pnpm test

  build:
    runs-on: ubuntu-latest
    needs: [test]
    steps:
    - uses: actions/checkout@v6
    - uses: actions/setup-node@v6
      with:
        node-version: 20
        cache: pnpm
    - run: pnpm install --frozen-lockfile
    - run: pnpm build

  deploy:
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    needs: [build]
    environment: production
    steps:
    - uses: aws-actions/configure-aws-credentials@v6
      with:
        role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
        aws-region: us-east-1
    - run: aws ecs update-service --cluster prod --service api --force-new-deployment
```

---

## GitLab CI: DAG Pipeline with OIDC

```yaml
stages:
  - setup
  - build
  - test
  - deploy

default:
  interruptible: true

variables:
  NODE_IMAGE: node:20-alpine

build:
  stage: build
  image: $NODE_IMAGE
  script:
    - npm ci --cache .npm
    - npm run build
  cache:
    key:
      files: [package-lock.json]
    paths: [.npm/]
  artifacts:
    paths: [dist/]

test-unit:
  stage: test
  needs: [build]
  image: $NODE_IMAGE
  script: npm test

test-e2e:
  stage: test
  needs: [build]
  image: $NODE_IMAGE
  script: npm run test:e2e
  rules:
    - changes:
      - src/**/*
      - tests/e2e/**/*

deploy-prod:
  stage: deploy
  needs: [test-unit, test-e2e]
  image: amazon/aws-cli:2.15.0
  id_tokens:
    GITLAB_OIDC_TOKEN:
      aud: https://gitlab.example.com
  script:
    - echo "${GITLAB_OIDC_TOKEN}" > /tmp/token
    - echo -e "[profile oidc]\nrole_arn=${AWS_ROLE_ARN}\nweb_identity_token_file=/tmp/token" > ~/.aws/config
    - aws ecs update-service --cluster prod --service api --force-new-deployment --profile oidc
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
  interruptible: false
```

---

## Monorepo Parent-Child Pipeline Generator (Python)

```python
import subprocess
import yaml

def get_changed_services(base_branch='origin/main'):
    result = subprocess.run(
        ['git', 'diff', '--name-only', base_branch],
        capture_output=True, text=True
    )
    changed = set()
    for f in result.stdout.strip().split('\n'):
        parts = f.split('/')
        if len(parts) > 1 and parts[0] == 'services':
            changed.add(parts[1])
    return changed

def generate_pipeline(services):
    pipeline = {'stages': ['build', 'test', 'deploy']}
    for svc in services:
        pipeline[f'build-{svc}'] = {
            'stage': 'build',
            'script': [f'cd services/{svc} && make build']
        }
        pipeline[f'test-{svc}'] = {
            'stage': 'test',
            'needs': [f'build-{svc}'],
            'script': [f'cd services/{svc} && make test']
        }
    return pipeline

if __name__ == '__main__':
    services = get_changed_services()
    if services:
        with open('child-pipeline.yml', 'w') as f:
            yaml.dump(generate_pipeline(services), f)
    else:
        with open('child-pipeline.yml', 'w') as f:
            f.write('no-op:\n  script: echo "No services changed"\n')
```
