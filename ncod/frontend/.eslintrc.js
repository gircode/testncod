module.exports = {
  root: true,
  env: {
    browser: true,
    node: true,
    es2021: true
  },
  extends: [
    'plugin:vue/vue3-recommended',
    'eslint:recommended',
    '@vue/typescript/recommended',
    '@vue/prettier',
    '@vue/prettier/@typescript-eslint'
  ],
  parserOptions: {
    ecmaVersion: 2021
  },
  rules: {
    'no-console': process.env.NODE_ENV === 'production' ? 'warn' : 'off',
    'no-debugger': process.env.NODE_ENV === 'production' ? 'warn' : 'off',
    // Vue属性顺序规则
    'vue/attributes-order': ['error', {
      order: [
        'DEFINITION', // is, v-is
        'LIST_RENDERING', // v-for
        'CONDITIONALS', // v-if, v-else-if, v-else, v-show, v-cloak
        'RENDER_MODIFIERS', // v-pre, v-once
        'GLOBAL', // id
        'UNIQUE', // ref, key
        'SLOT', // slot, v-slot
        'TWO_WAY_BINDING', // v-model
        'OTHER_DIRECTIVES', // v-custom-directive
        'OTHER_ATTR', // class, style, :prop="foo"
        'EVENTS', // @click="foo", v-on="foo"
        'CONTENT' // v-text, v-html
      ],
      alphabetical: false
    }],
    // 允许重复的函数名(因为有些工具函数可能在不同文件中有相同名称)
    'no-redeclare': 'off',
    '@typescript-eslint/no-redeclare': 'off',
    // 未使用的变量警告
    '@typescript-eslint/no-unused-vars': ['warn', {
      argsIgnorePattern: '^_',
      varsIgnorePattern: '^_',
      caughtErrorsIgnorePattern: '^_'
    }],
    // Vue组件命名规则
    'vue/multi-word-component-names': 'off',
    // Props 类型检查
    'vue/require-prop-types': 'error',
    // 组件标签顺序
    'vue/component-tags-order': ['error', {
      order: ['script', 'template', 'style']
    }],
    // template 中的缩进
    'vue/html-indent': ['error', 2],
    // 允许单行元素
    'vue/singleline-html-element-content-newline': 'off',
    // Props 命名规则
    'vue/prop-name-casing': ['error', 'camelCase'],
    // 组件名称大小写
    'vue/component-name-in-template-casing': ['error', 'PascalCase'],
    // 允许 v-html
    'vue/no-v-html': 'off'
  }
} 