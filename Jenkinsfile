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
                    python3 -m venv .venv
                    .venv/bin/python -m pip install -r requirements.txt
                    .venv/bin/python scripts/validate.py
                '''
            }
        }
    }

    post {
        always {
            cleanWs(notFailBuild: true)
        }
    }
}
