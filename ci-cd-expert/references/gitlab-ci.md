# GitLab CI/CD Reference

## DAG (Directed Acyclic Graph)

- `needs` bypasses stage sequence. Job starts instantly when listed dependencies finish.
- Stageless setup: empty `stages:`, use only `needs:` in all jobs.
- Fan-out/fan-in and diamond configurations supported.

### Full DAG Pipeline Example
```yaml
stages:
  - build
  - test
  - deploy

compile:
  stage: build
  script: npm run build
  artifacts:
    paths: [dist/]

test:unit:
  stage: test
  needs: [compile]
  script: npm run test:unit

test:integration:
  stage: test
  needs: [compile]
  script: npm run test:integration

deploy:prod:
  stage: deploy
  needs: [test:unit, test:integration]
  script: ./deploy.sh
```

---

## Dynamic Parent-Child Pipelines

- Generate child pipeline YAML dynamically at runtime.
- Parent writes child configuration to artifact, triggers execution.
- Monorepos: compute changed directories, generate jobs only for changed files.

### Dynamic Pipeline Setup
```yaml
# Parent pipeline configuration (.gitlab-ci.yml)
generate-pipeline:
  stage: build
  script: python3 generate-ci.py
  artifacts:
    paths: [child-pipeline.yml]

trigger-child:
  stage: test
  needs: [generate-pipeline]
  trigger:
    include:
      - artifact: child-pipeline.yml
        job: generate-pipeline
    strategy: depend
```

---

## Pipeline Efficiency

- `rules:`: filter job creation based on file changes (`changes:`), variables, or git branch state.
- `interruptible: true`: kill redundant, outdated runs automatically when new commit pushed to branch. Use globally inside `default:` block.
- `cache:key:files`: hash file contents for stable, cache-keyed workflows (e.g. `package-lock.json`).
- `cache:policy`: set `pull` for tests, `push` or `pull-push` for builds to avoid useless cache uploads.

### Optimization Example
```yaml
default:
  interruptible: true

cache:
  key:
    files:
      - package-lock.json
  paths:
    - .npm/
  policy: pull

build-app:
  script: npm ci --cache .npm && npm run build
  cache:
    policy: pull-push
  rules:
    - changes:
        - src/**/*
        - package-lock.json
```

---

## OIDC Federation

- `id_tokens`: request short-lived JSON Web Token (JWT) from GitLab.
- Avoid passing static long-lived cloud secret keys. Write JWT token to file and reference.
- Cloud providers (AWS, GCP, Vault) authenticate signature, issue temporary STS tokens.

### GitLab OIDC AWS Config
```yaml
deploy-aws:
  id_tokens:
    AWS_JWT_TOKEN:
      aud: https://gitlab.example.com
  before_script:
    - mkdir -p ~/.aws
    - echo "${AWS_JWT_TOKEN}" > /tmp/web_identity_token
    - echo -e "[profile oidc]\nrole_arn=${AWS_ROLE_ARN}\nweb_identity_token_file=/tmp/web_identity_token" > ~/.aws/config
  script:
    - aws sts get-caller-identity --profile oidc
    - aws s3 sync dist/ s3://my-prod-bucket/ --profile oidc
```
