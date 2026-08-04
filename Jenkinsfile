@Library('jenkins-pipelines@master') _

pipeline {
    agent {
        label 'gradle-long-running'
    }

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
            steps {
                checkout scm
            }
        }

        stage('Validate specifications') {
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
            when {
                branch 'main'
            }
            steps {
                sh '''
                    if [ -n "${GIT_PREVIOUS_SUCCESSFUL_COMMIT:-}" ]; then
                      git diff --name-only "$GIT_PREVIOUS_SUCCESSFUL_COMMIT" HEAD > changed-paths.txt
                    else
                      git show --pretty=format: --name-only HEAD > changed-paths.txt
                    fi
                    docker run --rm \
                      -e PIP_INDEX_URL -e PIP_CACHE_DIR=/pip-cache \
                      -e HTTP_PROXY -e HTTPS_PROXY -e NO_PROXY \
                      -v agent-eval-config-pip-cache:/pip-cache \
                      -v "$PWD:/workspace" -w /workspace \
                      python:3.12-slim sh -c \
                      'python -m pip install -r requirements.txt && python scripts/changed_agents.py --paths-file changed-paths.txt' \
                      > changed-agents.txt
                    echo "Changed AgentSpecs:"
                    cat changed-agents.txt
                '''
            }
        }

        stage('Trigger AgentEval') {
            when {
                branch 'main'
            }
            steps {
                script {
                    def configCommit = sh(
                        script: 'git rev-parse HEAD', returnStdout: true).trim()
                    def agents = fileExists('changed-agents.txt')
                        ? readFile('changed-agents.txt').readLines().findAll { it.trim() }
                        : []
                    for (String agentSpec : agents) {
                        build job: 'AgentEval/sandbox-runner', wait: true,
                              propagate: true, parameters: [
                            booleanParam(name: 'CONFIG_EVALUATION_ONLY', value: true),
                            string(name: 'CONFIG_COMMIT', value: configCommit),
                            string(name: 'AGENT_SPEC', value: agentSpec.trim()),
                            string(name: 'DATASET_SPEC', value: 'smoke@1')
                        ]
                    }
                }
            }
        }
    }

    post {
        always {
            cleanWs(notFailBuild: true)
        }
    }
}
