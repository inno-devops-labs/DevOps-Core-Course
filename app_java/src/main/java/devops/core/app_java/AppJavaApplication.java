package devops.core.app_java;

import devops.core.app_java.configuration.ServiceInfoProperties;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.EnableConfigurationProperties;

@SpringBootApplication
@EnableConfigurationProperties(ServiceInfoProperties.class)
public class AppJavaApplication {

	public static void main(String[] args) {
		SpringApplication.run(AppJavaApplication.class, args);
	}

}
