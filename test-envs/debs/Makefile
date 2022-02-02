all:
	$(MAKE) test || $(MAKE) clean fail
	$(MAKE) clean

.PHONY: setup
setup:
	terraform apply -auto-approve

.PHONY: test
test: setup
	[[ ! -f cw.json ]]
	poetry run awsclutter watch --dry-run > cw.json
	@echo "*** Check the cost for us-west-1 - should be \$$45.8"
	cat cw.json | jq -r '.[] | select(.MetricName=="DetachedEBSMonthlyCost") | select(.Dimensions | index({"Name": "RZCode", "Value": "us-west-1"})) | .Value'
	(( $$(echo "($$(cat cw.json | jq -r '.[] | select(.MetricName=="DetachedEBSMonthlyCost") | select(.Dimensions | index({"Name": "RZCode", "Value": "us-west-1"})) | .Value') - 45.8)^2 < (0.001^2)" | bc -l) ))
	@echo "*** Check the cost for us-east-2 - should be \$$4065.6"
	cat cw.json | jq -r '.[] | select(.MetricName=="DetachedEBSMonthlyCost") | select(.Dimensions | index({"Name": "RZCode", "Value": "us-east-2"})) | .Value'
	(( $$(echo "($$(cat cw.json | jq -r '.[] | select(.MetricName=="DetachedEBSMonthlyCost") | select(.Dimensions | index({"Name": "RZCode", "Value": "us-east-2"})) | .Value') - 4065.6)^2 < (0.001^2)" | bc -l) ))
	rm cw.json

.PHONY: clean
clean:
	terraform destroy -auto-approve
	[ $$(cat terraform.tfstate | jq '.resources | length') -eq 0 ]
	rm terraform.tfstate terraform.tfstate.backup

.PHONY: fail
fail:
	exit 1

.PHONY: grep-ebs
grep-ebs:
	@echo "*** ebs.tf has embedded comments with costs of resources per region - grep for these and sum ***"
	grep cost ebs.tf | grep 'us-west-1' | awk '{print $$NF}' | cut -c2- | awk '{s+=$$1} END {print s}'
	grep cost ebs.tf | grep 'us-east-2' | awk '{print $$NF}' | cut -c2- | awk '{s+=$$1} END {print s}'
