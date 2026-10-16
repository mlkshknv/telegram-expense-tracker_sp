// CI/CD pipeline для Telegram Expense Tracker
// Требования к Jenkins: плагины Pipeline, Git, JUnit, Credentials Binding;
// на агенте доступен Docker CLI (см. jenkins/docker-compose.yml).

pipeline {
    agent any

    // "на каждый коммит": локальный Jenkins недоступен для вебхуков GitHub,
    // поэтому он сам опрашивает репозиторий каждые 2 минуты.
    // При публичном адресе Jenkins можно использовать githubPush().
    triggers {
        pollSCM('H/2 * * * *')
    }

    parameters {
        booleanParam(name: 'PUSH_TO_DOCKERHUB', defaultValue: false,
                     description: 'Отправить образ в Docker Hub (нужны credentials dockerhub-creds)')
        booleanParam(name: 'DEPLOY_TO_MINIKUBE', defaultValue: false,
                     description: 'Развернуть образ в Minikube (CD, бонус)')
    }

    options {
        timestamps()
        buildDiscarder(logRotator(numToKeepStr: '15'))
        timeout(time: 20, unit: 'MINUTES')
        disableConcurrentBuilds()
    }

    environment {
        IMAGE_NAME = 'telegram-expense-tracker'
        DOCKERHUB_REPO = 'mlkshknv/telegram-expense-tracker'   // поменяйте на свой логин Docker Hub
        IMAGE_TAG = "${env.BUILD_NUMBER}"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                sh 'git log -1 --pretty=format:"%h %an: %s"'
            }
        }

        stage('Unit tests') {
            steps {
                // Тесты выполняются внутри Docker (этап "test" в Dockerfile),
                // поэтому на Jenkins не нужен Python, а окружение воспроизводимо.
                sh 'docker build --target test -t ${IMAGE_NAME}:test-${IMAGE_TAG} .'
                // Достаём JUnit-отчёт из тестового образа
                sh '''
                    mkdir -p reports
                    CID=$(docker create ${IMAGE_NAME}:test-${IMAGE_TAG})
                    docker cp $CID:/reports/junit.xml reports/junit.xml
                    docker rm $CID
                '''
            }
            post {
                always {
                    junit allowEmptyResults: true, testResults: 'reports/junit.xml'
                }
            }
        }

        stage('Build Docker image') {
            steps {
                sh 'docker build --target runtime -t ${IMAGE_NAME}:${IMAGE_TAG} -t ${IMAGE_NAME}:latest .'
                sh 'docker image ls ${IMAGE_NAME}'
            }
        }

        stage('Smoke test image') {
            steps {
                // Контейнер запускается, модуль импортируется, база создаётся в томе
                sh '''
                    docker run --rm ${IMAGE_NAME}:${IMAGE_TAG} \
                      python -c "import bot; bot.connect_db(); print('Smoke test OK:', bot.DB_PATH)"
                '''
            }
        }

        stage('Push to Docker Hub') {
            when { expression { params.PUSH_TO_DOCKERHUB } }
            steps {
                withCredentials([usernamePassword(credentialsId: 'dockerhub-creds',
                                                  usernameVariable: 'DH_USER',
                                                  passwordVariable: 'DH_TOKEN')]) {
                    sh '''
                        echo "$DH_TOKEN" | docker login -u "$DH_USER" --password-stdin
                        docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${DOCKERHUB_REPO}:${IMAGE_TAG}
                        docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${DOCKERHUB_REPO}:latest
                        docker push ${DOCKERHUB_REPO}:${IMAGE_TAG}
                        docker push ${DOCKERHUB_REPO}:latest
                        docker logout
                    '''
                }
            }
        }

        stage('Deploy to Minikube') {
            when { expression { params.DEPLOY_TO_MINIKUBE } }
            steps {
                // kubeconfig хранится в Jenkins как Secret file с id "minikube-kubeconfig";
                // образ берётся из Docker Hub, поэтому включите и PUSH_TO_DOCKERHUB
                withCredentials([file(credentialsId: 'minikube-kubeconfig', variable: 'KUBECONFIG')]) {
                    sh '''
                        kubectl apply -f k8s/
                        kubectl set image deployment/expense-bot expense-bot=${DOCKERHUB_REPO}:${IMAGE_TAG}
                        kubectl rollout status deployment/expense-bot --timeout=120s
                        kubectl get pods -l app=expense-bot
                    '''
                }
            }
        }
    }

    post {
        success { echo "Сборка #${env.BUILD_NUMBER} успешна: образ ${env.IMAGE_NAME}:${env.IMAGE_TAG}" }
        failure { echo 'Сборка упала — смотрите вывод стадии с ошибкой и отчёт тестов' }
        always {
            sh 'docker image rm ${IMAGE_NAME}:test-${IMAGE_TAG} || true'
        }
    }
}
