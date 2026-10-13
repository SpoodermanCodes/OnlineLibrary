pipeline {
    agent any

    environment {
        IMAGE_NAME      = 'online-library-ci'
        ANSIBLE_CONTAINER = 'ansible-docker-lab'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Docker Build') {
            steps {
                sh 'docker build -t $IMAGE_NAME .'
            }
        }

        stage('Pytest') {
            steps {
                sh 'docker run --rm $IMAGE_NAME python -m pytest test_app.py -v'
            }
        }

        stage('Ansible Deploy') {
            steps {
                sh 'docker exec $ANSIBLE_CONTAINER ansible-playbook -i /inventory.ini /docker-deploy.yml'
            }
        }

        stage('Verify') {
            steps {
                sh '''
                    sleep 5
                    docker ps --filter name=online-library-ansible
                    docker exec online-library-ansible python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:5000/health').read())"
                '''
            }
        }
    }

    post {
        success { echo 'Pipeline SUCCESS - Online Library deployed on http://localhost:5001' }
        failure { echo 'Pipeline FAILED - check the console output of the failed stage' }
    }
}
