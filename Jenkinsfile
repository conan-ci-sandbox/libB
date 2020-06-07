user_channel = "mycompany/stable"
config_url = "https://github.com/conan-ci-sandbox/settings.git"
conan_develop_repo = "conan-develop"
conan_tmp_repo = "conan-tmp"
artifactory_metadata_repo = "conan-metadata"

artifactory_url = (env.ARTIFACTORY_URL != null) ? "${env.ARTIFACTORY_URL}" : "jfrog.local"

reference_revision = null

def profiles = [
  "debug-gcc6": "conanio/gcc6",	
  "release-gcc6": "conanio/gcc6"	
]

def get_stages(profile, docker_image, lockfile_contents) {
    return {
        stage(profile) {
            node {
                docker.image(docker_image).inside("--net=host") {
                    def scmVars = checkout scm
                    withEnv(["CONAN_USER_HOME=${env.WORKSPACE}/conan_cache/"]) {
                        def lockfile = "${profile}.lock"
                        try {
                            stage("Configure Conan") {
                                sh "conan --version"
                                sh "conan config install ${config_url}"
                                withCredentials([usernamePassword(credentialsId: 'artifactory-credentials', usernameVariable: 'ARTIFACTORY_USER', passwordVariable: 'ARTIFACTORY_PASSWORD')]) {
                                    sh "conan user -p ${ARTIFACTORY_PASSWORD} -r ${conan_develop_repo} ${ARTIFACTORY_USER}"
                                    sh "conan user -p ${ARTIFACTORY_PASSWORD} -r ${conan_tmp_repo} ${ARTIFACTORY_USER}"
                                }
                            }

                            stage("Get package info") {       
                                name = sh (script: "conan inspect . --raw name", returnStdout: true).trim()
                                version = sh (script: "conan inspect . --raw version", returnStdout: true).trim()                                
                            }

                            if (lockfile_contents==null) {
                                stage("Create package") {       
                                    sh "conan graph lock . --profile ${profile} --lockfile=${lockfile} -r ${conan_develop_repo}"
                                    sh "cat ${lockfile}"
                                    sh "conan create . ${user_channel} --profile ${profile} --lockfile=${lockfile} -r ${conan_develop_repo} --ignore-dirty"
                                    sh "cat ${lockfile}"
                                }
                            }                         
                            else {
                                stage("Create package using lockfile") {       
                                    def lockfile_name = "${name}-${profile}.lock"
                                    writeFile file: lockfile_name, text: "${lockfile_contents}"
                                    sh "cat ${lockfile_name}"
                                    sh "conan create . ${user_channel} --lockfile ${lockfile_name} --ignore-dirty"
                                    sh "cat ${lockfile_name}"
                                    archiveArtifacts artifacts: lockfile_name, onlyIfSuccessful: true
                                    echo "archiveArtifacts: ${lockfile_name}"
                                    sh "cp ${lockfile_name} ${lockfile}"
                                }
                            }

                            stage("Get created package revision") {       
                                search_out = sh (script: "conan search ${name}/${version}@${user_channel} --revisions --raw", returnStdout: true).trim()    
                                reference_revision = search_out.split(" ")[0]
                                echo "${reference_revision}"
                            }

                            if (branch_name =~ ".*PR.*" || env.BRANCH_NAME == "develop") {                                      
                                stage("Upload package: ${name}/${version}#${reference_revision} to conan-tmp") {
                                    sh "conan upload '${name}/${version}' --all -r ${conan_tmp_repo} --confirm"
                                }

                            } 

                            stage("Upload lockfile") {
                                def lockfile_path = "/${artifactory_metadata_repo}/${env.JOB_NAME}/${env.BUILD_NUMBER}/${name}/${version}@${user_channel}/${profile}/${lockfile}"
                                def base_url = "http://${artifactory_url}:8081/artifactory"
                                def properties = "?properties=build.name=${env.JOB_NAME}%7Cbuild.number=${env.BUILD_NUMBER}%7Cprofile=${profile}%7Cname=${name}%7Cversion=${version}"
                                withCredentials([usernamePassword(credentialsId: 'artifactory-credentials', usernameVariable: 'ARTIFACTORY_USER', passwordVariable: 'ARTIFACTORY_PASSWORD')]) {
                                    // upload the lockfile
                                    sh "curl --user \"\${ARTIFACTORY_USER}\":\"\${ARTIFACTORY_PASSWORD}\" -X PUT ${base_url}${lockfile_path} -T ${lockfile}"
                                    // set properties in Artifactory for the file
                                    sh "curl --user \"\${ARTIFACTORY_USER}\":\"\${ARTIFACTORY_PASSWORD}\" -X PUT ${base_url}/api/storage${lockfile_path}${properties}"
                                }                                
                            }
                        }
                        finally {
                            deleteDir()
                        }
                    }
                }
            }
        }
    }
}

pipeline {
    agent none
    stages {

        stage('Build') {
            steps {
                script {
                    if (params.size()>0) {
                        parallel params.collectEntries { profile_name, lockfile ->
                            echo "${profile_name}"
                            echo "${lockfile}"
                            def docker_image = profiles[profile_name]
                            ["${profile_name}": get_stages(profile_name, docker_image, lockfile)]
                        }
                    }
                    else {
                        parallel profiles.collectEntries { profile, docker_image ->
                            ["${profile}": get_stages(profile, docker_image, null)]
                        }
                    }
                }
            }
        }

        stage("Trigger products pipeline") {
            agent any
            when {expression { return ((branch_name =~ ".*PR.*" || env.BRANCH_NAME == "develop") && params.size()==0) }}
            steps {
                script {
                    assert reference_revision != null
                    def reference = "${name}/${version}@${user_channel}#${reference_revision}"
                    build(job: "../products/master", propagate: true, parameters: [
                        [$class: 'StringParameterValue', name: 'reference', value: reference],
                        [$class: 'StringParameterValue', name: 'library_branch', value: env.BRANCH_NAME],
                    ]) 
                }
            }
        }
    }
}