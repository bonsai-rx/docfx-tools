// Licensed to the .NET Foundation under one or more agreements.
// The .NET Foundation licenses this file to you under the MIT license.

function removeBottomMargin(str){
  return str.split('').reverse().join('')
            .replace( '<p'.split('').reverse().join(''),
                      '<p style="margin-bottom:0;"'.split('').reverse().join('')
                    )
            .split('').reverse().join('');
}

// Strip IObservable and replace 'TSource' with 'Anything' 
function replaceIObservableAndTSource(str){
  if (str.includes('IGroupedObservable')){
    const re = new RegExp('<a.*IGroupedObservable.*&lt;');
    str = str.replace(re, '').replace('&gt;','').replace('&gt;','').replace('TSource', 'Anything');
  }
  else if (str.includes('IObservable')){
    const re = new RegExp('<a.*IObservable.*&lt;');
    str = str.replace(re, '').replace('&gt;','').replace('TSource', 'Anything');
    // can't combine re and '&gt;' into the same regex and do replaceAll because some classes have have two '&gt' in which case one of them is necessary
  }
  return str;
}

// compile list of data for input --> o --> output diagrams
function defineInputsAndOutputs(model){
  operators = [];
  if (model.oe.hubOrDevice === 'hub'){
    const hubChildrenLength = model.__global._shared['~/api/OpenEphys.Onix1.MultiDeviceFactory.yml'].children.length;
    for (let i = 0; i < hubChildrenLength; i++){
      if (model.__global._shared['~/api/OpenEphys.Onix1.MultiDeviceFactory.yml'].children[i].name[0].value.includes('Process')){
        description = [ 
          model.__global._shared['~/api/OpenEphys.Onix1.MultiDeviceFactory.yml'].children[i].summary, 
          model.__global._shared['~/api/OpenEphys.Onix1.MultiDeviceFactory.yml'].children[i].remarks
        ].join('');
      }
      input = {};
      if (model.__global._shared['~/api/OpenEphys.Onix1.MultiDeviceFactory.yml'].children[i].syntax.parameters && model.__global._shared['~/api/OpenEphys.Onix1.MultiDeviceFactory.yml'].children[i].syntax.parameters[0]){
        input = {
          'specName': replaceIObservableAndTSource(model.__global._shared['~/api/OpenEphys.Onix1.MultiDeviceFactory.yml'].children[i].syntax.parameters[0].type.specName[0].value),
          'name': model.__global._shared['~/api/OpenEphys.Onix1.MultiDeviceFactory.yml'].children[i].syntax.parameters[0].type.name[0].value.replaceAll(/(IObservable<)|(>)/g, ''),
          'description': removeBottomMargin([ model.__global._shared['~/api/OpenEphys.Onix1.MultiDeviceFactory.yml'].children[i].syntax.parameters[0].description, 
                                              model.__global._shared['~/api/OpenEphys.Onix1.MultiDeviceFactory.yml'].children[i].syntax.parameters[0].remarks].join(''))};
        input.internal = true;
      }
      output = {};
      dataFrame = [];
      if (model.__global._shared['~/api/OpenEphys.Onix1.MultiDeviceFactory.yml'].children[i].syntax.return){
        output = {
          'specName': replaceIObservableAndTSource(model.__global._shared['~/api/OpenEphys.Onix1.MultiDeviceFactory.yml'].children[i].syntax.return.type.specName[0].value),
          'name': model.__global._shared['~/api/OpenEphys.Onix1.MultiDeviceFactory.yml'].children[i].syntax.return.type.name[0].value.replaceAll(/(IObservable<)|(>)/g, ''),
          'description': removeBottomMargin([ model.__global._shared['~/api/OpenEphys.Onix1.MultiDeviceFactory.yml'].children[i].syntax.return.description, 
                                              model.__global._shared['~/api/OpenEphys.Onix1.MultiDeviceFactory.yml'].children[i].syntax.return.remarks].join(''))};
        output.internal = true;
        outputYml = [ '~/api/', 
                      model.__global._shared['~/api/OpenEphys.Onix1.MultiDeviceFactory.yml'].children[i].syntax.return.type.uid.replaceAll(/(\D*{)|(}$)/g, ''),  
                      '.yml'].join('');
        if (model['__global']['_shared'][outputYml] && model['__global']['_shared'][outputYml]['children'] && (model['__global']['_shared'][outputYml].type === 'class')){
          output.dataFrameDescription = [
            model['__global']['_shared'][outputYml].summary, 
            model['__global']['_shared'][outputYml].remarks].join('');
          const outputYmlChildrenLength = model['__global']['_shared'][outputYml]['children'].length;
          for (let j = 0; j < outputYmlChildrenLength; j++){
            if (model['__global']['_shared'][outputYml]['children'][j].type === 'property'){
              potentialEnumYml = '~/api/' + model['__global']['_shared'][outputYml]['children'][j].syntax.return.type.uid + '.yml';
              let enumFields = [];
              if (model['__global']['_shared'][potentialEnumYml] && (model['__global']['_shared'][potentialEnumYml]['type'] === 'enum')){
                enumFields = defineEnumFields(model['__global']['_shared'][potentialEnumYml]);
              }
                if (enumFields.length > 0){
                  output.dataFrameDescription = [
                    model['__global']['_shared'][outputYml].summary, 
                    model['__global']['_shared'][outputYml].remarks].join(''),
                  dataFrame.push({
                    'name': model['__global']['_shared'][outputYml]['children'][j].name[0].value, 
                    'type': model['__global']['_shared'][outputYml]['children'][j].syntax.return.type.specName[0].value, 
                    'description': removeBottomMargin([ model['__global']['_shared'][outputYml]['children'][j].summary, 
                                                        model['__global']['_shared'][outputYml]['children'][j].remarks].join('')),
                    'enumFields': enumFields,
                    'hasEnum': true
                  });
                }
                else{
                  dataFrame.push({
                    'name': model['__global']['_shared'][outputYml]['children'][j].name[0].value, 
                    'type': model['__global']['_shared'][outputYml]['children'][j].syntax.return.type.specName[0].value, 
                    'description': removeBottomMargin([ model['__global']['_shared'][outputYml]['children'][j].summary, 
                                                        model['__global']['_shared'][outputYml]['children'][j].remarks].join(''))
                  });                  
                }
            }
          }
        }
      }
    }
    if (Object.keys(input).length && Object.keys(dataFrame).length){
      operators.push({'description': description, 'input': input, 'output': output, 'dataFrame': dataFrame, 'hasInput': true, 'hasDataFrame': true});
    }
    else if (Object.keys(input).length){
      operators.push({'description': description, 'input': input, 'output': output, 'dataFrame': dataFrame, 'hasInput': true});
    }
    else if (Object.keys(dataFrame).length){
      operators.push({'description': description, 'input': input, 'output': output, 'dataFrame': dataFrame, 'hasDataFrame': true});
    }
    else{
      operators.push({'description': description, 'output': output});
    }
  }
  else if (model.children){
    const childrenLength = model.children.length;
    for (let i = 0; i < childrenLength; i++){
      if (model.children[i].uid.includes('Generate') || model.children[i].uid.includes('Process')){
        description = [model.children[i].summary, model.children[i].remarks].join('');
        input = {};
        if (model.children[i].syntax.parameters && model.children[i].syntax.parameters[0]){
          input = {
            'specName': replaceIObservableAndTSource(model.children[i].syntax.parameters[0].type.specName[0].value),
            'name': model.children[i].syntax.parameters[0].type.name[0].value.replaceAll(/(IObservable<)|(>)/g, ''),
            'description': removeBottomMargin([model.children[i].syntax.parameters[0].description, model.children[i].syntax.parameters[0].remarks].join(''))
          };
          input.dataFrame = [];
          if (model.__global._shared['~/api/OpenEphys.Onix1.' + input.name + '.yml']){
            input.internal = true;
            inputYml = [ '~/api/', 
                          model.children[i].syntax.parameters[0].type.uid.replaceAll(/(\D*{)|(}$)/g, ''),  
                          '.yml'].join('');
            if (model['__global']['_shared'][inputYml] && model['__global']['_shared'][inputYml]['children'] && (model['__global']['_shared'][inputYml].type === 'class')){
              input.dataFrameDescription = [
                model['__global']['_shared'][inputYml].summary, 
                model['__global']['_shared'][inputYml].remarks
              ].join('');
              const inputYmlChildrenLength = model['__global']['_shared'][inputYml]['children'].length;
              for (let j = 0; j < inputYmlChildrenLength; j++){
                if (model['__global']['_shared'][inputYml]['children'][j] && model['__global']['_shared'][inputYml]['children'][j].type === 'property'){
                  let enumFields = [];
                  if (model['__global']['_shared'][inputYml]['children'][j].syntax.parameters[0]){
                    potentialEnumYml = '~/api/' + model['__global']['_shared'][inputYml]['children'][j].syntax.parameters[0].type.uid + '.yml';
                    if (model['__global']['_shared'][potentialEnumYml] && (model['__global']['_shared'][potentialEnumYml]['type'] === 'enum')){
                      enumFields = defineEnumFields(model['__global']['_shared'][potentialEnumYml]);
                    }
                  }
                  if (enumFields.length > 0){
                    input.dataFrame.push({
                      'name': model['__global']['_shared'][inputYml]['children'][j].name[0].value, 
                      'type': model['__global']['_shared'][inputYml]['children'][j].syntax.return.type.specName[0].value, 
                      'description': removeBottomMargin([ model['__global']['_shared'][inputYml]['children'][j].summary, 
                                                          model['__global']['_shared'][inputYml]['children'][j].remarks].join('')),
                      'enumFields': enumFields,
                      'hasEnum': true
                    });
                  }
                  else{
                    input.dataFrame.push({
                      'name': model['__global']['_shared'][inputYml]['children'][j].name[0].value, 
                      'type': model['__global']['_shared'][inputYml]['children'][j].syntax.return.type.specName[0].value, 
                      'description': removeBottomMargin([ model['__global']['_shared'][inputYml]['children'][j].summary, 
                                                          model['__global']['_shared'][inputYml]['children'][j].remarks].join(''))
                    });                
                  }
                }
              }
            }
            else if (model['__global']['_shared'][inputYml] && model['__global']['_shared'][inputYml]['children'] && (model['__global']['_shared'][inputYml].type === 'enum')){
              input.internal = true;
              input.dataFrameDescription = [
                model['__global']['_shared'][inputYml].summary, 
                model['__global']['_shared'][inputYml].remarks
              ].join('');
              const inputYmlChildrenLength = model['__global']['_shared'][inputYml]['children'].length;
              for (let j = 0; j < inputYmlChildrenLength; j++){
                if (model['__global']['_shared'][inputYml]['children'][j].type === 'property'){
                  potentialEnumYml = '~/api/' + model['__global']['_shared'][inputYml]['children'][j].syntax.parameters[0].type.uid + '.yml';
                  let enumFields = [];
                  if (model['__global']['_shared'][potentialEnumYml] && (model['__global']['_shared'][potentialEnumYml]['type'] === 'enum')){
                    enumFields = defineEnumFields(model['__global']['_shared'][potentialEnumYml]);
                  }
                  if (enumFields.length > 0){
                    dataFrame.push({
                      'name': model['__global']['_shared'][inputYml]['children'][j].name[0].value, 
                      'type': model['__global']['_shared'][inputYml]['children'][j].syntax.return.type.specName[0].value, 
                      'description': removeBottomMargin([ model['__global']['_shared'][inputYml]['children'][j].summary, 
                                                          model['__global']['_shared'][inputYml]['children'][j].remarks].join('')),
                      'enumFields': enumFields,
                      'hasEnum': true
                    });
                  }
                  else{
                    dataFrame.push({
                      'name': model['__global']['_shared'][inputYml]['children'][j].name[0].value, 
                      'type': model['__global']['_shared'][inputYml]['children'][j].syntax.return.type.specName[0].value, 
                      'description': removeBottomMargin([ model['__global']['_shared'][inputYml]['children'][j].summary, 
                                                          model['__global']['_shared'][inputYml]['children'][j].remarks].join(''))
                    });                  
                  }
                }
              }
            }
          }
          else {
            input.external = true;
          }
        }
        if (model.children[i].syntax.return){
          output = {
            'specName': replaceIObservableAndTSource(model.children[i].syntax.return.type.specName[0].value),
            'name': model.children[i].syntax.return.type.name[0].value.replaceAll(/(IObservable<)|(>)/g, ''),
            'description': removeBottomMargin([model.children[i].syntax.return.description, model.children[i].syntax.return.remarks].join(''))};
          dataFrame = [];
          outputYml = [ '~/api/', 
                        model.children[i].syntax.return.type.uid.replaceAll(/(\D*{)|(}$)/g, ''),  
                        '.yml'].join('');
          if (model['__global']['_shared'][outputYml] && model['__global']['_shared'][outputYml]['children'] && (model['__global']['_shared'][outputYml].type === 'class')){
            output.internal = true;
            output.dataFrameDescription = [
              model['__global']['_shared'][outputYml].summary, 
              model['__global']['_shared'][outputYml].remarks].join('');
            const outputYmlChildrenLength = model['__global']['_shared'][outputYml]['children'].length;
            for (let j = 0; j < outputYmlChildrenLength; j++){
              if (model['__global']['_shared'][outputYml]['children'][j].type === 'property'){
                potentialEnumYml = '~/api/' + model['__global']['_shared'][outputYml]['children'][j].syntax.return.type.uid + '.yml';
                let enumFields = [];
                if (model['__global']['_shared'][potentialEnumYml] && (model['__global']['_shared'][potentialEnumYml]['type'] === 'enum')){
                  enumFields = defineEnumFields(model['__global']['_shared'][potentialEnumYml]);
                }
                if (enumFields.length > 0){
                  dataFrame.push({
                    'name': model['__global']['_shared'][outputYml]['children'][j].name[0].value, 
                    'type': model['__global']['_shared'][outputYml]['children'][j].syntax.return.type.specName[0].value, 
                    'description': removeBottomMargin([ model['__global']['_shared'][outputYml]['children'][j].summary, 
                                                        model['__global']['_shared'][outputYml]['children'][j].remarks].join('')),
                    'enumFields': enumFields,
                    'hasEnum': true
                  });
                }
                else{
                  dataFrame.push({
                    'name': model['__global']['_shared'][outputYml]['children'][j].name[0].value, 
                    'type': model['__global']['_shared'][outputYml]['children'][j].syntax.return.type.specName[0].value, 
                    'description': removeBottomMargin([ model['__global']['_shared'][outputYml]['children'][j].summary, 
                                                        model['__global']['_shared'][outputYml]['children'][j].remarks].join(''))
                  });                  
                }
              }
            }
          }
          if (dataFrame.length === 0 && input.dataFrame && input.dataFrame.length > 0){
            dataFrame = input.dataFrame;
            output.useInputDataFrame = true;;
          }
          else if (!output.internal) {
            output.external = true;
          }
          if (model['__global']['_shared'][outputYml] && model['__global']['_shared'][outputYml]['inheritedMembers']){
            output.internal = true;
            output.external = false;
            const inheritedMembersLength = model['__global']['_shared'][outputYml]['inheritedMembers'].length;
            for (let j = 0; j < inheritedMembersLength; j++){
              if (model['__global']['_shared'][outputYml]['inheritedMembers'][j].type === 'property'){
                let inheritedMemberYml = '~/api/' + model['__global']['_shared'][outputYml]['inheritedMembers'][j].parent + '.yml';
                if (model['__global']['_shared'][inheritedMemberYml]['children']){
                  let inheritedMemberChildrenLength = model['__global']['_shared'][inheritedMemberYml]['children'].length;
                  for (let k =  0; k < inheritedMemberChildrenLength; k++){
                    if (model['__global']['_shared'][outputYml]['inheritedMembers'][j].uid === model['__global']['_shared'][inheritedMemberYml]['children'][k].uid){
                      dataFrame.push({
                        'name': model['__global']['_shared'][outputYml]['inheritedMembers'][j].name[0].value, 
                        'type': model['__global']['_shared'][inheritedMemberYml]['children'][k].syntax.return.type.specName[0].value, 
                        'description':  removeBottomMargin([model['__global']['_shared'][inheritedMemberYml]['children'][k].summary, 
                                                            model['__global']['_shared'][inheritedMemberYml]['children'][k].remarks].join(''))
                      });
                    }
                  }
                }
              }
            }
          }
          else if (model['__global']['_shared'][outputYml] && model['__global']['_shared'][outputYml]['children'] && (model['__global']['_shared'][outputYml].type === 'enum')){
            output.internal = true;
            output.external = false;
            output.dataFrameDescription = [
              model['__global']['_shared'][outputYml].summary, 
              model['__global']['_shared'][outputYml].remarks
            ].join('');
            output.enumFields = defineEnumFields(model['__global']['_shared'][outputYml]);
            output.isEnum = true;
          }
          else if (!output.internal){
            output.external = true;
          }
        }
        if (Object.keys(input).length && Object.keys(dataFrame).length){
          operators.push({'description': description, 'input': input, 'output': output, 'dataFrame': dataFrame, 'hasInput': true, 'hasDataFrame': true});
        }
        else if (Object.keys(input).length){
          operators.push({'description': description, 'input': input, 'output': output, 'dataFrame': dataFrame, 'hasInput': true});
        }
        else if (Object.keys(dataFrame).length){
          operators.push({'description': description, 'input': input, 'output': output, 'dataFrame': dataFrame, 'hasDataFrame': true});
        }
        else {
          operators.push({'description': description, 'output': output});
        }
      }
    }
  }
  return operators;
}

// Define source or sink in documentation by checking for an explicit Category tag. If the class does not provide one,
// check the inheritance tree of the class. If the class inherits Bonsai.Sink and Bonsai.Combinator, ignore the Bonsai.Sink
// inheritance overrides the Bonsai.Combinator inheritance for determining whether an operator is a source or a combinator. This
// is because maybe sink operators inherit Bonsai.Combinator in addition to Bonsai.Sink.
function defineOperatorType(model){
  let operatorType = {'source': false, 'sink': false, 'combinator': false};
  if (model.syntax && model.syntax.content[0].value){
    if (model.syntax.content[0].value.includes('[WorkflowElementCategory(ElementCategory.Source)]')){
      operatorType.source = true;
    }
    else if (model.syntax.content[0].value.includes('[WorkflowElementCategory(ElementCategory.Sink)]')){
      operatorType.sink = true;
    }
    else if (model.syntax.content[0].value.includes('[WorkflowElementCategory(ElementCategory.Combinator)]')){
      operatorType.combinator = true;
    }
  }
  if (!(operatorType.source || operatorType.sink || operatorType.combinator)){
    if (model.inheritance){
      const inheritanceLength = model.inheritance.length;
      for (let i = 0; i < inheritanceLength; i++){
        if (model.inheritance[i].uid.includes('Bonsai.Source')){
          operatorType.source = true;
        }
        else if (model.inheritance[i].uid.includes('Bonsai.Sink')){
          operatorType.sink = true;
        }
        else if (model.inheritance[i].uid.includes('Bonsai.Combinator')){
          operatorType.combinator = true;
        }
        if (model.inheritance[i].uid.includes('OpenEphys.Onix1.MultiDeviceFactory')){
          operatorType.hub = true;
        }
        else if (model.inheritance[i].uid.includes('OpenEphys.Onix1.SingleDeviceFactory')){
          operatorType.device = true;
        }
      }
    }
  }
  operatorType.showWorkflow = operatorType.source | operatorType.sink | operatorType.combinator;
  return operatorType;
}

function defineSubOperators(model){
  let subOperators = []
  if (model.children){
    const childrenLength = model.children.length;
    for (let i = 0; i < childrenLength; i++){
      if (model.children[i].type === 'property'){
        potentialSubOperatorYml = '~/api/' + model.children[i].syntax.return.type.uid + '.yml';
        if (model['__global']['_shared'][potentialSubOperatorYml]){
          subOperatorChildrenLength = model['__global']['_shared'][potentialSubOperatorYml]['children'].length;
          let subProperties = [];
          for (let j = 0; j < subOperatorChildrenLength; j++){
            if (model['__global']['_shared'][potentialSubOperatorYml]['children'][j].type === 'property'){
              let enumFields = [];
              potentialEnumYml = '~/api/' + model['__global']['_shared'][potentialSubOperatorYml]['children'][j].syntax.return.type.uid + '.yml';
              if (model['__global']['_shared'][potentialEnumYml] && (model['__global']['_shared'][potentialEnumYml]['type'] === 'enum')){
                enumFields = defineEnumFields(model['__global']['_shared'][potentialEnumYml]);
              }
              if (enumFields.length > 0){
                subProperties.push({'name': model['__global']['_shared'][potentialSubOperatorYml]['children'][j].name[0].value,
                                    'type': model['__global']['_shared'][potentialSubOperatorYml]['children'][j].syntax.return.type.specName[0].value,
                                    'description': removeBottomMargin( [model['__global']['_shared'][potentialSubOperatorYml]['children'][j].summary, 
                                                                        model['__global']['_shared'][potentialSubOperatorYml]['children'][j].remarks].join('')),
                                    'enumFields': enumFields,
                                    'hasEnum': true});
              }
              else{
                subProperties.push({'name': model['__global']['_shared'][potentialSubOperatorYml]['children'][j].name[0].value,
                                    'type': model['__global']['_shared'][potentialSubOperatorYml]['children'][j].syntax.return.type.specName[0].value,
                                    'description': removeBottomMargin( [model['__global']['_shared'][potentialSubOperatorYml]['children'][j].summary, 
                                                                        model['__global']['_shared'][potentialSubOperatorYml]['children'][j].remarks].join(''))
                });
              }
            }
          }
          if (subProperties.length > 0){
            subOperators.push({
              'object': model.children[i].name[0].value,
              'type': model.children[i].syntax.return.type.specName[0].value,
              'subProperties': subProperties,
              'hasSubProperties': true,
              'subOperator': true
            });
          }
          else if (model.__global._shared['~/api/' + model.children[i].name[0].value + '.yml']){
            subOperators.push({
              'object': model.children[i].name[0].value,
              'type': model.children[i].syntax.return.type.specName[0].value,
              'subOperator': true
            });
          }
        }
      }
    }
  }
  return subOperators
}

// compile list of properties
function defineProperties(model){
  properties = [];
  if (model.children){
    const childrenLength = model.children.length;
    for (let i = 0; i < childrenLength; i++){
      if (model.children[i].type === 'property'){
        potentialEnumYml = '~/api/' + model['children'][i].syntax.return.type.uid + '.yml';
        let enumFields = [];
        if (model['__global']['_shared'][potentialEnumYml] && (model['__global']['_shared'][potentialEnumYml]['type'] === 'enum')){
          enumFields = defineEnumFields(model['__global']['_shared'][potentialEnumYml]);
        }
        if (enumFields.length > 0){
          properties.push({
            'name': model.children[i].name[0].value, 
            'type': model.children[i].syntax.return.type.specName[0].value, 
            'description': removeBottomMargin([model.children[i].summary, model.children[i].remarks].join('')),
            'enumFields': enumFields,
            'hasEnum': true
          });
        }
        else { 
          properties.push({
            'name': model.children[i].name[0].value, 
            'type': model.children[i].syntax.return.type.specName[0].value, 
            'description': removeBottomMargin([model.children[i].summary, model.children[i].remarks].join(''))
          });
        }
      }
    }
  }
  if (model.inheritedMembers){
    const inheritedMembersLength = model.inheritedMembers.length;
    for (let i = 0; i < inheritedMembersLength; i++){
      if (model.inheritedMembers[i].type && (model.inheritedMembers[i].type === 'property')){
        let inheritedMemberYml = '~/api/' + model.inheritedMembers[i].parent + '.yml';
        if (model['__global']['_shared'][inheritedMemberYml]['children']){
          let inheritedMemberChildrenLength = model['__global']['_shared'][inheritedMemberYml]['children'].length;
          for (let j =  0; j < inheritedMemberChildrenLength; j++){
            if (model.inheritedMembers[i].uid === model['__global']['_shared'][inheritedMemberYml]['children'][j].uid){
              properties.push(
                {'name': model.inheritedMembers[i].name[0].value, 
                'type': model['__global']['_shared'][inheritedMemberYml]['children'][j].syntax.return.type.specName[0].value, 
                'description':  removeBottomMargin([model['__global']['_shared'][inheritedMemberYml]['children'][j].summary, 
                                                    model['__global']['_shared'][inheritedMemberYml]['children'][j].remarks].join(''))
              });
            }
          }
        }
      }
    }
  }
  return properties;
}

function sortProperties(properties){
  let propertyNames = [];
  let propertyNamesThatFitPattern = [];
  const propertiesLength = properties.length;
  for (let i = 0; i < propertiesLength; i++){
    propertyNames.push([properties[i].name, 
                        /\D+\d+$/.test(properties[i].name), 
                        String(properties[i].name.match(/\D+/)), 
                        Number(properties[i].name.match(/\d+$/))]);
  }
  for (let i = 0; i < propertiesLength; i++){
    if (propertyNames[i][1]){
      if (!propertyNamesThatFitPattern.includes(propertyNames[i][2])){
        propertyNamesThatFitPattern.push(propertyNames[i][2]);
      }
    }
  }
  const propertyNamesThatFitPatternLength = propertyNamesThatFitPattern.length;
  for (let j = 0; j < propertyNamesThatFitPatternLength; j++){
    for (let i = 1; i < propertiesLength; i++){
      for (let k = i; k > 0; k--){
        if ((propertyNames[k][2] === propertyNamesThatFitPattern[j]) && (propertyNames[k - 1][2] === propertyNamesThatFitPattern[j])){
          if (propertyNames[k][3] < propertyNames[k - 1][3]){
            swapElements(properties, k, k - 1);
            swapElements(propertyNames, k, k - 1); // why does this need to be here for this sortProperties function to work?
          }
        }
      }
    }
  }
  return properties;
}

const swapElements = (array, index1, index2) => {
  const temp = array[index1];
  array[index1] = array[index2];
  array[index2] = temp;
};

function defineEnumFields(model){
  let enumFields = [];
  if (model.children){
    const childrenLength = model.children.length;
    for (let i = 0; i < childrenLength; i++){
      if (model.children[i].type === 'field'){
        enumFields.push({
          'field&value': model.children[i].syntax.content[0].value,
          'description': removeBottomMargin([ model.children[i].summary, 
                                              model.children[i].remarks].join(''))
        });
      }
    }
  }
  return enumFields;
}


/**
 * This method will be called at the start of exports.transform in ManagedReference.html.primary.js
 */
exports.preTransform = function (model) {
  
  model.oe = {};
  
  model.oe.description = [model.summary, model.remarks].join('');

  operatorType = defineOperatorType(model);
  if (operatorType.source){
    model.oe.operatorType = 'source';
  }
  else if (operatorType.sink){
    model.oe.operatorType = 'sink';
  }
  else if (operatorType.combinator){
    model.oe.operatorType = 'combinator';
  }

  if (operatorType.showWorkflow) {
    model.showWorkflow = operatorType.showWorkflow;
  }
  else {

  }

  if (operatorType.device) {
    model.oe.hubOrDevice = 'device';
    model.oe.device = true;
  }
  else if (operatorType.hub){
    model.oe.hubOrDevice = 'hub';
    model.oe.hub = true;
  }
  
  operators = defineInputsAndOutputs(model);
  if (operators.length > 0){
    model.oe.operators = operators;
  }

  properties = defineProperties(model);
  if (properties.length > 0){
    model.oe.hasProperties = true;
    model.oe.properties = sortProperties(properties);
  }
  
  subOperators = defineSubOperators(model);
  if (subOperators.length > 0){
    model.oe.hasSubOperators = true;
    model.oe.subOperators = subOperators;
  }

  if (model.oe.hasProperties && model.oe.hasSubOperators){
    subPropertyNames = [];
    hubProperties = [];
    const subOperatorsLength = model.oe.subOperators.length;
    for (let i = 0; i < subOperatorsLength; i++){
      subPropertyNames.push(model.oe.subOperators[i].object);
    }
    const propertiesLength = model.oe.properties.length;
    for (let i = 0; i < propertiesLength; i++){
      const subPropertyNamesLength = subPropertyNames.length;
      propertyNotInSubOperator = false;
      for (let j = 0; j < subPropertyNamesLength; j++){
        if (model.oe.properties[i].name === subPropertyNames[j]){
          propertyNotInSubOperator = true;
        }
      }
      if (!propertyNotInSubOperator){
        hubProperties.push(model.oe.properties[i]);
      }
    }
    if (hubProperties.length > 0){
      model.oe.subOperators.push({
        'object': 'Misc',
        'subProperties': hubProperties,
        'hasSubProperties': true,
        'subOperator': false
      })
    }
  }

  enumFields = defineEnumFields(model);
  if (enumFields.length > 0){
    model.oe.hasEnumFields = true;
    model.oe.enumFields = enumFields;
  }

  if (model.uid.includes('DeviceFactory')){
    model.showWorkflow = false;
  }

  return model;
}

/**
 * This method will be called at the end of exports.transform in ManagedReference.html.primary.js
 */
exports.postTransform = function (model) {
  return model;
}
