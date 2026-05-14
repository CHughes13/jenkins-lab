pipeline {
    // agent any = run this pipeline on any available Jenkins agent/executor
    agent any

    stages {

        stage('Cleanup') {
            steps {
                sh '''
                    # Stop and remove containers if they exist
                    # -f flag = force remove even if container is running
                    docker rm -f flask-app nginx-proxy || true

                    # Remove old images if they exist
                    # This ensures we always build fresh images
                    # -f flag = force remove
                    docker rmi -f flask-app nginx-proxy || true
                '''
            }
        }

        stage('Setup Network') {
            steps {
                sh '''
                    # Create a Docker network for the containers to communicate on
                    # Containers on the same network can find each other by name
                    # e.g. nginx can reach flask at http://flask-app:5000
                    # || true = if network already exists, ignore the error and continue
                    docker network create app-network || true
                '''
            }
        }

        stage('Build Images') {
            steps {
                sh '''
                    # Build the Flask app image
                    # -t = tag/name for the image
                    # -f = specify which Dockerfile to use
                    # . = build context, means use current directory for files
                    docker build -t flask-app -f Dockerfile.flask .

                    # Build the Nginx image
                    docker build -t nginx-proxy -f Dockerfile.nginx .
                '''
            }
        }

        stage('Deploy Containers') {
            steps {
                sh '''
                    # Run the Flask container on the network
                    # -d = detached mode, runs in background
                    # --name = give the container a name
                    # --network = connect to our app-network
                    # Not exposed to outside world, only accessible within the network
                    docker run -d --name flask-app --network app-network flask-app

                    # Run the Nginx container on the network
                    # -p 80:80 = map port 80 on EC2 to port 80 in container
                    # This is the only container exposed to the outside world
                    # All traffic goes through Nginx first, then to Flask
                    docker run -d --name nginx-proxy --network app-network -p 80:80 nginx-proxy
                '''
            }
        }

    }
}