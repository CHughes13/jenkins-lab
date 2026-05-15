pipeline {
    // agent any = run this pipeline on any available Jenkins agent/executor
    agent any

    stages {

        // ============================================
        // STAGE 1: TRIVY FILESYSTEM SCAN
        // Scans source code & requirements.txt for known vulnerabilities
        // This runs first because there's no point building anything if your dependencies are compromised
        // ============================================

        stage('Trivy FS Scan') {
            steps {
                sh '''
                    # Scan current workspace directory (your repo)
                    # --format json = output as structured JSON which is machine-readable
                    # --output = save results to a file instead of just printing
                    # .= current directory (where Jenkins checked out your code)
                    trivy fs --format json --output trivy-fs-results.json .
                '''
            }
            post {
                // 'always' means results will be archived whether vulnerabiliies are found or not
                always {
                    archiveArtifacts artifacts: 'trivy-fs-results.json', allowEmptyArchive: true
                }
            }

        }

        // ============================================
        // STAGE 2: UNIT TESTS
        // Run tests BEFORE building Docker images
        // Why? Tests are fast, Docker builds are slow
        // Best to find out if code is broken now, don't want to waste time building
        // ============================================

        stage('Unit Tests') {
            steps {
                // catchError = if test fails, DON'T kill the whole pipeline
                // Instead gets marked as UNSTABLE (yellow) and keeps going
                // This means you still get Trivy image scan results etc.

                catchError(buildResult: 'UNSTABLE', stageResult: 'FAILURE') {
                    sh '''
                        # Create a virtual environment - an isolated Python installation
                        # so we don't pollute Jenkins server w/ packages
                        python3 -m venv .venv

                        # Activate virtual environment. Dot is shorthand for 'source'
                        . .venv/bin/activate

                        # Install Flask - needed because test_app.py imports app.py which uses Flask
                        pip install -r requirements.txt

                        # Run the unit tests
                        # -m unittest = run python's unittest module
                        # test_app = the file to look for tests in (w/o .py extension)
                        python3 -m unittest test_app

                        # Exit virtual environment (this is gd practice/cleanup)
                        deactivate
                    '''
                }
            
            }


        }

        // ============================================
        // STAGE 3: CLEANUP
        // Remove old containers and images from previous pipeline runs
        // Why? Docker won't let you create a container w/ same name as one that already exists
        // Makes a clear slate before rebuilding
        // ============================================

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

        // ============================================
        // STAGE 4: SETUP NETWORK
        // Create a Docker network so containers can talk to each other
        // Why? By default containers are isolated
        // Shared network lets containers find each other by name (can't do this outside network)
        // ============================================

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

        // ============================================
        // STAGE 5: BUILD IMAGES
        // Build Docker images from our Dockerfiles
        // Why separate Dockerfiles? Each container has a different job:
        // - flask-app: runs the Python application
        // - nginx-proxy: acts as a reverse proxy, forwarding traffic to Flask
        // ============================================

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

        // ============================================
        // STAGE 6: TRIVY IMAGE SCAN
        // Scans the BUILT image for vulnerabilities
        // Why scan again? Because your base image (e.g. python:3.11)
        // contains OS packages that might have their own vulnerabilities.
        // The FS scan only checked YOUR code
        // This checks EVERYTHING in final container = your code + base image + system packages
        // ============================================

        stage('Trivy Image Scan') {
            steps {
                sh '''
                    # First command: print human-readable results to console
                    # --severity HIGH,CRITICAL = only show the serious stuff
                    # This is what you'll see in the Jenkins console output
                    trivy image --severity HIGH,CRITICAL flask-app

                    # Second command: save full detailed results as JSON
                    # This gets archived for records/auditing
                    trivy image --format json --output trivy-image-results.json flask-app
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'trivy-image-results.json', allowEmptyArchive: true
                }
            }
        }

        // ============================================
        // STAGE 7: GATE - MANUAL APPROVAL
        // Pipeline PAUSES here and waits for a human to click
        // "Proceed" or "Abort" in the Jenkins UI
        // This gives someone a chance to review the Trivy results before deploying to production.
        // ============================================
        
        stage('Approve Deployment') {
            steps {
                // input = pause and wait for human approval
                // The message is what the person sees in the Jenkins UI
                input message: 'Review Trivy scan results. Proceed with deployment?'
            }
        }


        // ============================================
        // STAGE 8: DEPLOY CONTAINERS
        // Only runs if someone clicks "Proceed"
        // Run the containers on our network
        // Why two containers? This is a common production pattern:
        // - Flask handles the application logic
        // - Nginx sits in front as a reverse proxy (handles SSL, load balancing, static files)
        // Only Nginx is exposed to the outside world (port 80). Flask is internal only.
        // ============================================

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