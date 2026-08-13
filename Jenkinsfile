@Library('jenkins-pipelines@master') _

pipeline {
    agent none

    options {
        ansiColor('xterm')
        buildDiscarder(logRotator(numToKeepStr: '20'))
        disableConcurrentBuilds(abortPrevious: true)
        skipDefaultCheckout(true)
        timeout(time: 15, unit: 'MINUTES')
    }

    environment {
        PIP_INDEX_URL = 'https://mirrors.cloud.tencent.com/pypi/simple/'
        PIP_CACHE_DIR = '/tmp/agent-eval-config-pip-cache'
    }

    stages {
        stage('Checkout') {
            agent {
                label 'gradle-long-running'
            }
            steps {
                checkout scm
            }
        }

        stage('Validate specifications') {
            agent {
                label 'gradle-long-running'
            }
            steps {
                sh '''
                    docker run --rm \
                      -e PIP_INDEX_URL -e PIP_CACHE_DIR=/pip-cache \
                      -e HTTP_PROXY -e HTTPS_PROXY -e NO_PROXY \
                      -v agent-eval-config-pip-cache:/pip-cache \
                      -v "$PWD:/workspace" -w /workspace \
                      python:3.12-slim sh -c \
                      'python -m pip install -r requirements.txt && python scripts/validate.py'
                '''
            }
        }

        stage('Resolve changed agents') {
            agent {
                label 'gradle-long-running'
            }
            when {
                branch 'main'
            }
            steps {
                sh '''
                    if [ -n "${GIT_PREVIOUS_SUCCESSFUL_COMMIT:-}" ]; then
                      git diff --name-only "$GIT_PREVIOUS_SUCCESSFUL_COMMIT" HEAD > changed-paths.txt
                    else
                      for revisions in agents/*/revisions; do
                        find "$revisions" -maxdepth 1 -type f -name '*.yaml' | sort | tail -n 1
                      done > changed-paths.txt
                    fi
                    docker run --rm \
                      -e PIP_INDEX_URL -e PIP_CACHE_DIR=/pip-cache \
                      -e HTTP_PROXY -e HTTPS_PROXY -e NO_PROXY \
                      -v agent-eval-config-pip-cache:/pip-cache \
                      -v "$PWD:/workspace" -w /workspace \
                      python:3.12-slim sh -c \
                      'python -m pip install -q -r requirements.txt >/dev/null && python scripts/changed_agents.py --paths-file changed-paths.txt' \
                      > changed-agents.txt
                    echo "Changed AgentSpecs:"
                    cat changed-agents.txt
                '''
                script {
                    env.CONFIG_COMMIT = sh(
                        script: 'git rev-parse HEAD', returnStdout: true).trim()
                    env.CHANGED_AGENT_SPECS = readFile('changed-agents.txt').trim()
                }
            }
        }

        stage('Trigger AgentEval') {
            when {
                branch 'main'
            }
            steps {
                script {
                    def configCommit = env.CONFIG_COMMIT
                    def agents = env.CHANGED_AGENT_SPECS
                        ? env.CHANGED_AGENT_SPECS.readLines().findAll { it.trim() }
                        : []
                    for (String agentSpec : agents) {
                        def safeAgent = agentSpec.trim().split('@')[0]
                        def runId = "config-${env.BUILD_NUMBER}-${safeAgent}-${configCommit.take(8)}"
                        build job: 'AgentEval-evaluate-agent', wait: true,
                              propagate: true, parameters: [
                            string(name: 'RUN_ID', value: runId),
                            string(name: 'CONFIG_COMMIT', value: configCommit),
                            string(name: 'AGENT_SPEC', value: agentSpec.trim()),
                            string(name: 'DATASET_SPEC', value: 'smoke@4'),
                            string(name: 'RUNNER_IMAGE', value:
                                'ghcr.io/openprojectx/agent-eval-runner@sha256:8969045f249172ceb11bfceb8cfec400ce9b52b36045c8dc991e87d0f37bd06e'),
                            string(name: 'POLICY_REVISION', value: 'audit-v1')
                        ]
                    }
                }
            }
        }
    }

    post {
        always {
            node('gradle-long-running') {
                cleanWs(notFailBuild: true)
            }
        }
    }
}
