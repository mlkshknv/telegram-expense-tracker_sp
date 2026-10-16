# Assignment 5: запуск CI/CD (Docker + Jenkins)

Пошаговая инструкция для воспроизведения pipeline на своём компьютере (Windows/macOS/Linux).

## 0. Что нужно установить
- Docker Desktop (или Docker Engine) — проверка: `docker version`
- Git
- (бонус) Minikube и kubectl

## 1. Проверить Docker-образ вручную
```bash
git clone https://github.com/mlkshknv/telegram-expense-tracker_sp.git
cd telegram-expense-tracker_sp

docker build --target test -t telegram-expense-tracker:test .      # запускает pytest
docker build --target runtime -t telegram-expense-tracker:latest . # рабочий образ
docker run --rm -e BOT_TOKEN=<токен> -v expense-data:/app/data telegram-expense-tracker:latest
```
📸 Скриншот 1: успешная сборка (`5 passed`) и `docker image ls`.

## 2. Запустить Jenkins
```bash
docker compose -f jenkins/docker-compose.yml up -d --build
docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```
Открыть http://localhost:8080 → ввести пароль → **Install suggested plugins** → создать пользователя.

## 3. Создать Pipeline-задачу
1. **New Item** → имя `telegram-expense-tracker` → **Pipeline** → OK.
2. **Pipeline → Definition:** *Pipeline script from SCM*.
3. **SCM:** Git, Repository URL: `https://github.com/mlkshknv/telegram-expense-tracker_sp.git`
4. **Branch Specifier:** `*/main`, **Script Path:** `Jenkinsfile` → Save.
5. **Build Now** (первый запуск также включает опрос репозитория `pollSCM`).

📸 Скриншот 2: Stage View со всеми зелёными стадиями.
📸 Скриншот 3: Console Output (стадия Unit tests, `5 passed`).
📸 Скриншот 4: Test Result (JUnit-отчёт).

## 4. Проверить запуск «на каждый коммит»
Сделайте небольшой коммит (например, в README) и `git push`. В течение ~2 минут Jenkins
сам запустит новую сборку (в истории будет «Started by an SCM change»).

📸 Скриншот 5: сборка, запущенная SCM change.

## 5. (опционально) Push в Docker Hub
1. Docker Hub → Account settings → Personal access tokens → создать токен.
2. Jenkins → Manage Jenkins → Credentials → Global → **Username with password**,
   ID: `dockerhub-creds`, логин Docker Hub + токен.
3. В `Jenkinsfile` поменять `DOCKERHUB_REPO` на `<логин>/telegram-expense-tracker`.
4. **Build with Parameters** → отметить `PUSH_TO_DOCKERHUB`.

📸 Скриншот 6: образ на странице Docker Hub.

## 6. (бонус) CD в Minikube
```bash
minikube start --driver=docker
kubectl create secret generic expense-bot-secret --from-literal=BOT_TOKEN=<токен>
docker network connect minikube jenkins        # Jenkins видит API-сервер Minikube
kubectl config view --flatten --minify > kubeconfig-jenkins.yaml
```
В `kubeconfig-jenkins.yaml` замените адрес `server:` на `https://minikube:8443`.
Jenkins → Credentials → **Secret file**, ID `minikube-kubeconfig`, загрузить файл (после этого удалить его локально).
Запустить **Build with Parameters** с `PUSH_TO_DOCKERHUB` и `DEPLOY_TO_MINIKUBE`.

📸 Скриншот 7: `kubectl get pods` со статусом Running.

## Частые проблемы
| Симптом | Решение |
|---|---|
| `permission denied ... docker.sock` | контейнер Jenkins запущен не от root — проверьте `user: root` в compose |
| `docker: not found` в Jenkins | Jenkins собран не из `jenkins/Dockerfile` — пересоберите с `--build` |
| Тесты не видны в Test Result | проверьте, что стадия Unit tests создала `reports/junit.xml` |
| `Conflict: terminated by other getUpdates request` | одновременно запущены два экземпляра бота (локально и в Kubernetes) — оставьте один |
